#!/usr/bin/env python3
"""
FastAPI GUI for Stanford Research Systems PS310 High Voltage Power Supply
Provides a web interface for controlling the PS310 with voltage ramping features.
"""

import sys
import os
from pathlib import Path

# Note: Virtual environment path for reference in documentation
# Not modifying sys.executable to avoid unexpected side effects
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
if os.name == "nt":
    venv_python = os.path.join(venv_path, "Scripts", "python.exe")
else:
    venv_python = os.path.join(venv_path, "bin", "python3")

if not os.path.exists(venv_python):
    venv_python = sys.executable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import logging
import traceback
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

# Import the StanfordPS310 driver
try:
    from libs.StanfordPS310 import StanfordPS310
except ImportError:
    StanfordPS310 = None

# PyVISA is used for VISA device discovery
try:
    import pyvisa
except ImportError:
    pyvisa = None

app = FastAPI(title="Stanford PS310 Power Supply GUI", version="1.0.0")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stanfordps310_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Timing constants for queue and polling
_MIN_COMMAND_DELAY = 0.25  # 250ms minimum delay between PS310 commands
_VOLTAGE_POLL_INTERVAL = 0.5  # 500ms interval for voltage polling

# Command queue for serializing PS310 interactions
class CommandPriority(Enum):
    """Priority levels for command queue."""
    HIGH = 0    # Critical operations (disconnect, emergency stop)
    NORMAL = 1  # Regular operations (set voltage, etc.)
    LOW = 2     # Background polling

@dataclass
class QueuedCommand:
    """Represents a command to be executed on the PS310."""
    priority: CommandPriority
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    future: Optional[asyncio.Future] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
    
    def __lt__(self, other):
        """Enable priority queue ordering."""
        return self.priority.value < other.priority.value

# Global state for the power supply
ps310_instance: Optional[StanfordPS310] = None
ps310_state = {
    "connected": False,
    "address": None,
    "output_enabled": False,
    "set_voltage": 0.0,
    "actual_voltage": 0.0,
    "current": 0.0,
    "ramping": False,
    "ramp_progress": 0,
    "error": None
}

# Queue and background tasks
command_queue: Optional[asyncio.PriorityQueue] = None
queue_processor_task: Optional[asyncio.Task] = None
voltage_poller_task: Optional[asyncio.Task] = None
ramp_task: Optional[asyncio.Task] = None
queue_sequence_counter = 0  # For maintaining FIFO order within same priority
queue_sequence_lock: Optional[asyncio.Lock] = None  # Thread safety for counter

async def queue_command(func: Callable, *args, priority: CommandPriority = CommandPriority.NORMAL, **kwargs):
    """
    Add a command to the queue and wait for its result.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        priority: Command priority level
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function execution
    """
    global command_queue, queue_sequence_counter, queue_sequence_lock
    
    if command_queue is None:
        raise RuntimeError("Command queue not initialized")
    
    # Create a future to get the result
    future = asyncio.Future()
    
    # Add sequence number to maintain FIFO within same priority (with thread safety)
    async with queue_sequence_lock:
        queue_sequence_counter += 1
        sequence = queue_sequence_counter
    
    # PriorityQueue requires items to be comparable
    # Use tuple: (priority, sequence, command) for proper ordering
    command = QueuedCommand(priority=priority, func=func, args=args, kwargs=kwargs, future=future)
    await command_queue.put((priority.value, sequence, command))
    
    # Wait for the command to be executed
    return await future

async def process_command_queue():
    """
    Background task that processes commands from the queue with proper delays.
    Ensures minimum 250ms delay between PS310 interactions.
    """
    global command_queue, ps310_instance
    
    logger.info("Command queue processor started")
    last_execution_time = 0
    
    while True:
        try:
            # Get next command from queue
            priority_val, sequence, command = await command_queue.get()
            
            # Ensure minimum 250ms delay between commands
            current_time = time.time()
            time_since_last = current_time - last_execution_time
            if time_since_last < _MIN_COMMAND_DELAY:
                delay_needed = _MIN_COMMAND_DELAY - time_since_last
                await asyncio.sleep(delay_needed)
            
            # Execute the command
            try:
                if asyncio.iscoroutinefunction(command.func):
                    result = await command.func(*command.args, **command.kwargs)
                else:
                    result = command.func(*command.args, **command.kwargs)
                
                # Set the result in the future
                if command.future and not command.future.done():
                    command.future.set_result(result)
                    
            except Exception as e:
                logger.error(f"Error executing queued command: {e}", exc_info=True)
                if command.future and not command.future.done():
                    command.future.set_exception(e)
            
            last_execution_time = time.time()
            command_queue.task_done()
            
        except asyncio.CancelledError:
            logger.info("Command queue processor cancelled")
            break
        except Exception as e:
            logger.error(f"Error in command queue processor: {e}", exc_info=True)
            await asyncio.sleep(0.1)

async def poll_voltage():
    """
    Background task that polls voltage every 500ms to update the display.
    Runs at lower priority to not interfere with user commands.
    """
    global ps310_instance, ps310_state, command_queue
    
    logger.info("Voltage poller started")
    
    while True:
        try:
            # Only poll if connected
            if ps310_instance and ps310_state["connected"]:
                try:
                    # Queue the voltage measurement at low priority
                    voltage = await queue_command(
                        ps310_instance.measure_voltage,
                        priority=CommandPriority.LOW
                    )
                    ps310_state["actual_voltage"] = voltage
                except Exception as e:
                    logger.debug(f"Error polling voltage: {e}")
            
            # Wait for next poll cycle
            await asyncio.sleep(_VOLTAGE_POLL_INTERVAL)
                    
        except asyncio.CancelledError:
            logger.info("Voltage poller cancelled")
            break
        except Exception as e:
            logger.error(f"Error in voltage poller: {e}", exc_info=True)
            await asyncio.sleep(1)

async def start_background_tasks():
    """Initialize and start background tasks."""
    global command_queue, queue_processor_task, voltage_poller_task, queue_sequence_lock
    
    if command_queue is None:
        command_queue = asyncio.PriorityQueue()
        queue_sequence_lock = asyncio.Lock()
        queue_processor_task = asyncio.create_task(process_command_queue())
        voltage_poller_task = asyncio.create_task(poll_voltage())
        logger.info("Background tasks started")

async def stop_background_tasks():
    """Stop and cleanup background tasks."""
    global queue_processor_task, voltage_poller_task, command_queue, queue_sequence_lock
    
    if voltage_poller_task:
        voltage_poller_task.cancel()
        try:
            await voltage_poller_task
        except asyncio.CancelledError:
            pass
        voltage_poller_task = None
    
    if queue_processor_task:
        queue_processor_task.cancel()
        try:
            await queue_processor_task
        except asyncio.CancelledError:
            pass
        queue_processor_task = None
    
    command_queue = None
    queue_sequence_lock = None
    logger.info("Background tasks stopped")

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the server starts."""
    await start_background_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up background tasks when the server shuts down."""
    await stop_background_tasks()

@app.get("/", response_class=HTMLResponse)
async def power_supply_gui():
    """Main power supply control GUI."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stanford PS310 High Voltage Power Supply Control</title>
        
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            /* Octicon SVG styling */
            .octicon {
                display: inline-block;
                vertical-align: text-bottom;
                fill: currentColor;
            }
            
            /* Connection Toolbar */
            .connection-toolbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px 20px;
                background: rgba(44, 62, 80, 0.95);
                border-bottom: 2px solid rgba(102, 126, 234, 0.3);
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            }
            
            .connection-toolbar-left {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .connection-toolbar-status {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #ecf0f1;
                font-size: 14px;
            }
            
            .toolbar-btn {
                background: rgba(108, 117, 125, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px 12px;
                cursor: pointer;
                color: #ecf0f1;
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s;
                white-space: nowrap;
            }
            
            .toolbar-btn:hover {
                background: rgba(108, 117, 125, 0.5);
                border-color: rgba(102, 126, 234, 0.6);
            }
            
            .toolbar-btn:active {
                background: rgba(108, 117, 125, 0.7);
            }
            
            .toolbar-btn-primary {
                background: #667eea;
                border-color: #667eea;
            }
            
            .toolbar-btn-primary:hover {
                background: #764ba2;
                border-color: #764ba2;
            }
            
            /* Settings button and popover */
            .settings-btn {
                background: rgba(108, 117, 125, 0.3);
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                cursor: pointer;
                color: #ecf0f1;
                font-size: 11px;
                display: inline-flex;
                align-items: center;
                gap: 4px;
                transition: background 0.2s;
            }
            
            .settings-btn:hover {
                background: rgba(108, 117, 125, 0.5);
            }
            
            /* Modal backdrop */
            .modal-backdrop {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
                display: none;
            }
            
            .modal-backdrop.show {
                display: block;
            }
            
            /* Connection Modal */
            .connection-modal {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border: 2px solid #667eea;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
                z-index: 1000;
                display: none;
                min-width: 400px;
                max-width: 500px;
            }
            
            .connection-modal.show {
                display: block;
            }
            
            .connection-modal h3 {
                margin: 0 0 20px 0;
                color: #333;
                font-size: 1.4em;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .connection-modal .form-group {
                margin-bottom: 15px;
            }
            
            .connection-modal .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
            }
            
            .connection-modal .form-group select,
            .connection-modal .form-group input {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            
            .connection-modal .form-group select:focus,
            .connection-modal .form-group input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .connection-modal .form-group small {
                display: block;
                margin-top: 5px;
                color: #666;
                font-size: 0.85em;
            }
            
            .connection-modal .btn-group {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            
            .connection-modal .btn {
                flex: 1;
            }
            
            /* Settings popover */
            .settings-popover {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
                z-index: 1000;
                display: none;
                min-width: 250px;
            }
            
            .settings-popover.show {
                display: block;
            }
            
            .settings-popover h4 {
                margin: 0 0 15px 0;
                color: #333;
                font-size: 1em;
            }
            
            .settings-popover .form-group {
                margin-bottom: 15px;
            }
            
            .settings-popover .form-group:last-child {
                margin-bottom: 0;
            }
            
            .settings-popover label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #555;
                font-size: 0.9em;
            }
            
            .settings-popover input {
                width: 100%;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            
            .settings-popover input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .settings-popover .btn-group {
                display: flex;
                gap: 8px;
                margin-top: 10px;
            }
            
            .settings-popover .btn {
                padding: 8px 16px;
                font-size: 14px;
            }
            
            /* Scope plot container */
            .scope-plot-container {
                background: #2c3e50;
                border-radius: 8px;
                padding: 0;
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            .scope-plot-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .scope-plot-header h3 {
                margin: 0;
                font-size: 0.9em;
                color: #ecf0f1;
                opacity: 0.9;
            }
            
            .scope-plot-canvas {
                width: 100%;
                height: 120px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                background: rgba(0, 0, 0, 0.2);
            }
            
            .main-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                padding: 30px;
            }
            
            @media (max-width: 900px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
            }
            
            .panel {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                border-left: 4px solid #667eea;
            }
            
            /* Compact styling for Control panel */
            .panel-control {
                padding: 10px;
            }
            
            .panel-control h2 {
                margin-bottom: 6px;
                font-size: 1.4em;
            }
            
            .panel-control h3 {
                margin-top: 12px;
                margin-bottom: 6px;
                font-size: 1.1em;
            }
            
            .panel-control .form-group {
                margin-bottom: 6px;
            }
            
            .panel-control .form-group label {
                margin-bottom: 4px;
                font-size: 0.95em;
            }
            
            .panel-control .form-group input {
                padding: 7px;
                font-size: 15px;
            }
            
            .panel-control .form-group small {
                margin-top: 2px;
                font-size: 0.85em;
            }
            
            .panel-control .form-row {
                margin-bottom: 6px;
                gap: 8px;
            }
            
            .panel-control .btn-group {
                margin-top: 6px;
                margin-bottom: 6px;
                gap: 6px;
            }
            
            .panel-control .btn {
                padding: 9px 18px;
                font-size: 15px;
            }
            
            .panel-control .ramp-plot-wrapper {
                margin: 1px 0;
                padding: 3px;
            }
            
            .panel-control .ramp-plot-wrapper h3 {
                margin: 0 0 1px 0;
                font-size: 1.0em;
            }
            
            .panel-control .ramp-plot-wrapper canvas {
                max-height: 160px;
                display: block;
            }
            
            .panel-control .ramp-controls {
                gap: 10px;
            }
            
            .panel-control .progress-bar {
                height: 22px;
                margin: 8px 0;
            }
            
            /* Gap between right column panels */
            .panel-gap {
                margin-top: 20px;
            }
            
            .panel h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.5em;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
                animation: pulse 2s infinite;
            }
            
            .status-indicator.connected {
                background: #28a745;
            }
            
            .status-indicator.disconnected {
                background: #dc3545;
            }
            
            .status-indicator.ramping {
                background: #ffc107;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
            }
            
            .form-group input[type="text"],
            .form-group input[type="number"],
            .form-group select {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            .form-group input[type="text"]:focus,
            .form-group input[type="number"]:focus,
            .form-group select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .form-group input[readonly] {
                background-color: #f8f9fa;
                color: #6c757d;
                cursor: not-allowed;
            }
            
            .form-group input.invalid {
                border-color: #dc3545;
                background-color: #fff5f5;
            }
            
            .form-group small {
                display: block;
                margin-top: 5px;
                color: #666;
                font-size: 0.9em;
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .form-row .form-group {
                margin-bottom: 0;
            }
            
            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                display: inline-block;
                text-align: center;
            }
            
            .btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .btn-primary:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-success {
                background: #28a745;
                color: white;
            }
            
            .btn-success:hover:not(:disabled) {
                background: #218838;
                transform: translateY(-2px);
            }
            
            .btn-danger {
                background: #dc3545;
                color: white;
            }
            
            .btn-danger:hover:not(:disabled) {
                background: #c82333;
                transform: translateY(-2px);
            }
            
            .btn-warning {
                background: #ffc107;
                color: #333;
            }
            
            .btn-warning:hover:not(:disabled) {
                background: #e0a800;
                transform: translateY(-2px);
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover:not(:disabled) {
                background: #5a6268;
                transform: translateY(-2px);
            }
            
            .btn-group {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            /* Inline ramp info layout */
            .ramp-actions-container {
                display: flex;
                align-items: stretch;
                gap: 15px;
                margin-top: 8px;
            }
            
            .ramp-info-inline {
                flex: 1;
                min-width: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding: 0 8px;
            }
            
            .ramp-info-inline .info-line {
                color: #666;
                font-size: 0.75em;
                line-height: 1.3;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .ramp-info-inline .info-line:first-child {
                font-weight: 600;
                color: #555;
            }
            
            .btn-full {
                width: 100%;
            }
            
            .display-panel {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 20px;
            }
            
            .display-voltage-info {
                flex: 0 0 auto;
                text-align: center;
                min-width: 200px;
            }
            
            .display-value {
                font-size: 3em;
                font-weight: bold;
                margin: 10px 0;
                font-family: 'Courier New', monospace;
            }
            
            .display-label {
                font-size: 1.2em;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .display-scope-plot {
                flex: 1;
                min-width: 0;
            }
            
            .display-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .display-small {
                background: #34495e;
                padding: 15px;
                border-radius: 8px;
            }
            
            .display-small .display-value {
                font-size: 1.8em;
            }
            
            .display-small .display-label {
                font-size: 0.9em;
            }
            
            .alert {
                padding: 6px 12px;
                border-radius: 4px;
                margin-left: 10px;
                display: none;
                font-size: 0.75em;
                vertical-align: middle;
            }
            
            .alert.show {
                display: inline-block;
            }
            
            .alert-info {
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
            }
            
            .alert-success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            
            .alert-warning {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }
            
            .alert-danger {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            
            .progress-bar {
                width: 100%;
                height: 30px;
                background: #e9ecef;
                border-radius: 15px;
                overflow: hidden;
                margin: 15px 0;
                display: none;
            }
            
            .progress-bar.show {
                display: block;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                transition: width 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .info-item {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
            
            .info-item-label {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 5px;
            }
            
            .info-item-value {
                font-size: 1.2em;
                font-weight: 600;
                color: #333;
            }
            
            .ramp-controls {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .safety-warning {
                background: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
            }
            
            .safety-warning h3 {
                color: #856404;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .safety-warning ul {
                margin-left: 20px;
                color: #856404;
            }
            
            .safety-warning li {
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <!-- Modal backdrop -->
        <div class="modal-backdrop" id="modalBackdrop"></div>
        
        <!-- Connection Modal -->
        <div class="connection-modal" id="connectionModal">
            <h3>
                <span id="connectionStatus" class="status-indicator disconnected"></span>
                Connection Settings
            </h3>
            
            <div class="form-group">
                <label for="visaAddress">VISA Address:</label>
                <select id="visaAddress">
                    <option value="">Loading devices...</option>
                </select>
                <small>Select the GPIB address of the PS310</small>
            </div>
            
            <div class="btn-group">
                <button id="connectBtn" class="btn btn-success" onclick="connectDevice()">
                    🔌 Connect
                </button>
                <button id="disconnectBtn" class="btn btn-danger" onclick="disconnectDevice()" disabled>
                    🔌 Disconnect
                </button>
            </div>
            
            <div class="btn-group">
                <button class="btn btn-secondary" onclick="refreshVisaDevices()">
                    🔄 Refresh Devices
                </button>
                <button class="btn btn-secondary" onclick="closeConnectionModal()">
                    Close
                </button>
            </div>
        </div>
        
        <div class="container">
            <div class="header">
                <h1>⚡ Stanford PS310 High Voltage Power Supply</h1>
            </div>
            
            <!-- Connection Toolbar -->
            <div class="connection-toolbar">
                <div class="connection-toolbar-left">
                    <div class="connection-toolbar-status">
                        <span id="toolbarConnectionStatus" class="status-indicator disconnected"></span>
                        <span id="toolbarConnectionText">Disconnected</span>
                    </div>
                    <button class="toolbar-btn toolbar-btn-primary" onclick="openConnectionModal()">
                        ⚙️ Connection
                    </button>
                </div>
                <div id="toolbarAlertPanel" class="alert"></div>
            </div>
            
            <div class="main-content">
                <!-- Left Column: Control -->
                <div>
                    
                    <!-- Control Panel (Combined Manual Control + Voltage Ramping) -->
                    <div class="panel panel-control">
                        <h2>🎛️ Control</h2>
                        
                        <!-- Manual Voltage Control -->
                        <h3 style="color: #555; font-size: 1.2em;">Manual Voltage</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="setVoltage">Set Voltage (V):</label>
                                <input type="number" id="setVoltage" value="-50" step="0.1" min="-1250" max="-50">
                                <small>Range: -1250V to -50V</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="currentLimit">Current Limit (mA):</label>
                                <input type="number" id="currentLimit" value="10" step="0.1" min="0" max="21">
                                <small>Range: 0 to 21 mA</small>
                            </div>
                        </div>
                        
                        <div class="form-row" style="gap: 8px;">
                            <button id="setVoltageBtn" class="btn btn-primary" style="flex: 1;" onclick="setVoltage()" disabled>
                                📝 Set Voltage
                            </button>
                            <button id="setCurrentBtn" class="btn btn-primary" style="flex: 1;" onclick="setCurrent()" disabled>
                                ⚡ Set Current
                            </button>
                        </div>
                        
                        <!-- Voltage Ramping -->
                        <h3 style="color: #555; font-size: 1.2em; display: flex; align-items: center; gap: 10px;">
                            <span id="rampingStatus" class="status-indicator disconnected"></span>
                            Voltage Ramping
                        </h3>
                        
                        <div class="ramp-controls">
                            <div class="form-group">
                                <label for="rampStart">Start Voltage (V):</label>
                                <input type="number" id="rampStart" value="0.0" step="0.1" min="-1250" max="0" readonly>
                                <small>Automatically set to current Set Voltage</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="rampEnd">End Voltage (V):</label>
                                <input type="number" id="rampEnd" value="-50" step="0.1" min="-1250" max="0">
                            </div>
                            
                            <div class="form-group">
                                <label for="rampStep">Step Size (V):</label>
                                <input type="number" id="rampStep" value="10" step="0.1" min="0.1" max="100">
                            </div>
                            
                            <div class="form-group">
                                <label for="rampDelay">Delay (seconds):</label>
                                <input type="number" id="rampDelay" value="1" step="0.1" min="0.1" max="60">
                            </div>
                        </div>
                        
                        <!-- Ramp Visualization Plot -->
                        <div class="ramp-plot-wrapper" style="background: white; border-radius: 6px; padding: 3px; border: 2px solid #e9ecef;">
                            <h3 style="margin: 0 0 1px 0; font-size: 1.0em; color: #333;">📈 Ramp Preview</h3>
                            <canvas id="rampPlot" width="460" height="160" style="width: 100%; max-width: 460px; height: auto; display: block;"></canvas>
                        </div>
                        
                        <div class="progress-bar" id="rampProgress">
                            <div class="progress-fill" id="rampProgressFill" style="width: 0%">0%</div>
                        </div>
                        
                        <div class="ramp-actions-container">
                            <button id="startRampBtn" class="btn btn-primary" onclick="startRamp()" disabled>
                                🚀 Start Ramp
                            </button>
                            <button id="stopRampBtn" class="btn btn-danger" onclick="stopRamp()" disabled>
                                🛑 Stop Ramp
                            </button>
                            <div class="ramp-info-inline">
                                <div class="info-line">Ramp Info</div>
                                <div class="info-line" id="rampInfo">Configure ramp parameters above</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Right Column: Monitoring & Output Control -->
                <div>
                    <!-- Display Panel -->
                    <div class="panel">
                        <h2>📊 Live Readings</h2>
                        
                        <div class="display-panel">
                            <div class="display-voltage-info">
                                <div class="display-label">Actual Voltage</div>
                                <div class="display-value" id="displayActualVoltage">0.0 V</div>
                            </div>
                            
                            <!-- Scope Plot -->
                            <div class="display-scope-plot">
                                <div class="scope-plot-container">
                                    <div class="scope-plot-header">
                                        <div style="position: relative; margin-left: auto;">
                                            <button class="settings-btn" id="scopeSettingsBtn" onclick="toggleScopeSettings()">
                                                <svg class="octicon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="12" height="12">
                                                    <path fill-rule="evenodd" d="M7.429 1.525a6.593 6.593 0 011.142 0c.036.003.108.036.137.146l.289 1.105c.147.56.55.967.997 1.189.174.086.341.183.501.29.417.278.97.423 1.53.27l1.102-.303c.11-.03.175.016.195.046.219.31.41.641.573.989.014.031.022.11-.059.19l-.815.806c-.411.406-.562.957-.53 1.456a4.588 4.588 0 010 .582c-.032.499.119 1.05.53 1.456l.815.806c.08.08.073.159.059.19a6.494 6.494 0 01-.573.99c-.02.029-.086.074-.195.045l-1.103-.303c-.559-.153-1.112-.008-1.529.27-.16.107-.327.204-.5.29-.449.222-.851.628-.998 1.189l-.289 1.105c-.029.11-.101.143-.137.146a6.613 6.613 0 01-1.142 0c-.036-.003-.108-.037-.137-.146l-.289-1.105c-.147-.56-.55-.967-.997-1.189a4.502 4.502 0 01-.501-.29c-.417-.278-.97-.423-1.53-.27l-1.102.303c-.11.03-.175-.016-.195-.046a6.492 6.492 0 01-.573-.989c-.014-.031-.022-.11.059-.19l.815-.806c.411-.406.562-.957.53-1.456a4.587 4.587 0 010-.582c.032-.499-.119-1.05-.53-1.456l-.815-.806c-.08-.08-.073-.159-.059-.19a6.44 6.44 0 01.573-.99c.02-.029.086-.075.195-.045l1.103.303c.559.153 1.112.008 1.529-.27.16-.107.327-.204.5-.29.449-.222.851-.628.998-1.189l.289-1.105c.029-.11.101-.143.137-.146zM8 0c-.236 0-.47.01-.701.03-.743.065-1.29.615-1.458 1.261l-.29 1.106c-.017.066-.078.158-.211.224a5.994 5.994 0 00-.668.386c-.123.082-.233.09-.299.071l-1.103-.303c-.644-.176-1.392.021-1.82.63a7.977 7.977 0 00-.704 1.217c-.315.675-.111 1.422.363 1.891l.815.806c.05.048.098.147.088.294a6.084 6.084 0 000 .772c.01.147-.038.246-.088.294l-.815.806c-.474.469-.678 1.216-.363 1.891.2.428.436.835.704 1.218.428.609 1.176.806 1.82.63l1.103-.303c.066-.019.176-.011.299.071.213.143.436.272.668.386.133.066.194.158.212.224l.289 1.106c.169.646.715 1.196 1.458 1.26a8.094 8.094 0 001.402 0c.743-.064 1.29-.614 1.458-1.26l.29-1.106c.017-.066.078-.158.211-.224a5.98 5.98 0 00.668-.386c.123-.082.233-.09.299-.071l1.103.303c.644.176 1.392-.021 1.82-.63.268-.382.505-.79.704-1.217.315-.675.111-1.422-.364-1.891l-.814-.806c-.05-.048-.098-.147-.088-.294a6.1 6.1 0 000-.772c-.01-.147.039-.246.088-.294l.814-.806c.475-.469.679-1.216.364-1.891a7.992 7.992 0 00-.704-1.218c-.428-.609-1.176-.806-1.82-.63l-1.103.303c-.066.019-.176.011-.299-.071a5.991 5.991 0 00-.668-.386c-.133-.066-.194-.158-.212-.224L10.16 1.29C9.99.645 9.444.095 8.701.031A8.094 8.094 0 008 0zm1.5 8a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM11 8a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                                </svg>
                                            </button>
                                            <div class="settings-popover" id="scopeSettingsPopover">
                                                <h4>Scope Settings</h4>
                                                <div class="form-group">
                                                    <label for="scopeTimeWindow">Time Window (seconds):</label>
                                                    <input type="number" id="scopeTimeWindow" value="30" min="5" max="300" step="5">
                                                </div>
                                                <div class="btn-group">
                                                    <button class="btn btn-primary" onclick="applyScopeSettings()">Apply</button>
                                                    <button class="btn btn-secondary" onclick="closeScopeSettings()">Cancel</button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <canvas id="scopePlot" class="scope-plot-canvas" width="400" height="120"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <div class="display-row">
                            <div class="display-small">
                                <div class="display-label">Set Voltage</div>
                                <div class="display-value" id="displaySetVoltage">0.0 V</div>
                            </div>
                            <div class="display-small">
                                <div class="display-label">Current</div>
                                <div class="display-value" id="displayCurrent">0.0 mA</div>
                            </div>
                        </div>
                        
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-item-label">Output Status</div>
                                <div class="info-item-value" id="displayOutputStatus">OFF</div>
                            </div>
                            <div class="info-item">
                                <div class="info-item-label">Connection</div>
                                <div class="info-item-value" id="displayConnection">Disconnected</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Output Control Panel -->
                    <div class="panel panel-gap">
                        <h2>⚡ Output Control</h2>
                        
                        <div class="btn-group">
                            <button id="outputOnBtn" class="btn btn-success" onclick="setOutput(true)" disabled>
                                ⚡ Output ON
                            </button>
                            <button id="outputOffBtn" class="btn btn-danger" onclick="setOutput(false)" disabled>
                                🔴 Output OFF
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let updateInterval = null;
            
            // Voltage history for scope plot
            let voltageHistory = [];
            let scopeTimeWindow = 30; // seconds
            
            // Smooth scrolling animation state
            let animationFrameId = null;
            let lastRealVoltage = null;
            let currentRealVoltage = null;
            let lastRealTimestamp = null;
            let currentRealTimestamp = null;
            
            // Initialize the GUI
            window.addEventListener('load', function() {
                refreshVisaDevices();
                startStatusUpdates();
                startSmoothAnimation(); // Start smooth scrolling animation
                drawScopePlot(); // Initial draw
            });
            
            // Open connection modal
            function openConnectionModal() {
                const modal = document.getElementById('connectionModal');
                const backdrop = document.getElementById('modalBackdrop');
                modal.classList.add('show');
                backdrop.classList.add('show');
            }
            
            // Close connection modal
            function closeConnectionModal() {
                const modal = document.getElementById('connectionModal');
                const backdrop = document.getElementById('modalBackdrop');
                modal.classList.remove('show');
                backdrop.classList.remove('show');
            }
            
            // Close modal when clicking on backdrop
            document.addEventListener('DOMContentLoaded', function() {
                const backdrop = document.getElementById('modalBackdrop');
                if (backdrop) {
                    backdrop.addEventListener('click', function(e) {
                        if (e.target === backdrop) {
                            closeConnectionModal();
                            closeScopeSettings();
                        }
                    });
                }
            });
            
            // Refresh VISA devices
            async function refreshVisaDevices() {
                try {
                    const response = await fetch('/list_visa_resources');
                    const data = await response.json();
                    
                    const select = document.getElementById('visaAddress');
                    select.innerHTML = '';
                    
                    if (data.error) {
                        select.innerHTML = '<option value="">Error: ' + data.error + '</option>';
                        showAlert('danger', 'Error scanning for devices: ' + data.error);
                    } else if (data.resources.length === 0) {
                        select.innerHTML = '<option value="">No GPIB devices found</option>';
                        showAlert('warning', 'No GPIB devices found. Check connections.');
                    } else {
                        select.innerHTML = '<option value="">-- Select a device --</option>';
                        data.resources.forEach(resource => {
                            if (resource.includes('GPIB')) {
                                const option = document.createElement('option');
                                option.value = resource;
                                option.textContent = resource;
                                select.appendChild(option);
                            }
                        });
                        showAlert('success', `Found ${data.resources.filter(r => r.includes('GPIB')).length} GPIB device(s)`);
                    }
                } catch (error) {
                    console.error('Error refreshing devices:', error);
                    showAlert('danger', 'Failed to scan for devices: ' + error.message);
                }
            }
            
            // Connect to device
            async function connectDevice() {
                const address = document.getElementById('visaAddress').value;
                
                if (!address) {
                    showAlert('warning', 'Please select a VISA address');
                    return;
                }
                
                try {
                    showAlert('info', 'Connecting to PS310...');
                    const response = await fetch('/connect', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({address: address})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('success', 'Connected to PS310 successfully!');
                        updateConnectionState(true);
                        closeConnectionModal(); // Close modal on successful connection
                    } else {
                        showAlert('danger', 'Connection failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Connection error:', error);
                    showAlert('danger', 'Connection error: ' + error.message);
                }
            }
            
            // Disconnect from device
            async function disconnectDevice() {
                try {
                    const response = await fetch('/disconnect', {method: 'POST'});
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('info', 'Disconnected from PS310');
                        updateConnectionState(false);
                    } else {
                        showAlert('danger', 'Disconnect failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Disconnect error:', error);
                    showAlert('danger', 'Disconnect error: ' + error.message);
                }
            }
            
            // Set voltage
            async function setVoltage() {
                const voltage = parseFloat(document.getElementById('setVoltage').value);
                
                if (isNaN(voltage) || voltage > 0 || voltage < -1250) {
                    showAlert('warning', 'Invalid voltage. Must be between -1250V and 0V');
                    return;
                }
                
                try {
                    // Set voltage only
                    const response = await fetch('/set_voltage', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({voltage: voltage})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('success', `Voltage set to ${voltage}V`);
                    } else {
                        showAlert('danger', 'Set voltage failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Set voltage error:', error);
                    showAlert('danger', 'Set voltage error: ' + error.message);
                }
            }
            
            // Set current limit
            async function setCurrent() {
                const currentLimit = parseFloat(document.getElementById('currentLimit').value);
                
                if (isNaN(currentLimit) || currentLimit < 0 || currentLimit > 21) {
                    showAlert('warning', 'Invalid current. Must be between 0 and 21 mA');
                    return;
                }
                
                try {
                    // Set current limit only
                    const response = await fetch('/set_current_limit', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({current: currentLimit / 1000})  // Convert mA to A
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('success', `Current limit set to ${currentLimit} mA`);
                    } else {
                        showAlert('danger', 'Set current failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Set current error:', error);
                    showAlert('danger', 'Set current error: ' + error.message);
                }
            }
            
            // Set output state
            async function setOutput(state) {
                try {
                    const response = await fetch('/set_output', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({state: state})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('success', `Output ${state ? 'ENABLED' : 'DISABLED'}`);
                    } else {
                        showAlert('danger', 'Set output failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Set output error:', error);
                    showAlert('danger', 'Set output error: ' + error.message);
                }
            }
            
            // Start voltage ramp
            async function startRamp() {
                const start = parseFloat(document.getElementById('rampStart').value);
                const end = parseFloat(document.getElementById('rampEnd').value);
                const step = parseFloat(document.getElementById('rampStep').value);
                const delay = parseFloat(document.getElementById('rampDelay').value);
                
                // Validation
                if (isNaN(start) || isNaN(end) || isNaN(step) || isNaN(delay)) {
                    showAlert('warning', 'Please enter valid ramp parameters');
                    return;
                }
                
                if (start > 0 || start < -1250 || end > 0 || end < -1250) {
                    showAlert('warning', 'Voltages must be between -1250V and 0V');
                    return;
                }
                
                if (step <= 0) {
                    showAlert('warning', 'Step size must be positive');
                    return;
                }
                
                try {
                    const response = await fetch('/start_ramp', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            start: start,
                            end: end,
                            step: step,
                            delay: delay
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('info', 'Voltage ramp started');
                        document.getElementById('rampProgress').classList.add('show');
                        document.getElementById('startRampBtn').disabled = true;
                        document.getElementById('stopRampBtn').disabled = false;
                        document.getElementById('rampingStatus').className = 'status-indicator ramping';
                    } else {
                        showAlert('danger', 'Start ramp failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Start ramp error:', error);
                    showAlert('danger', 'Start ramp error: ' + error.message);
                }
            }
            
            // Stop voltage ramp
            async function stopRamp() {
                try {
                    const response = await fetch('/stop_ramp', {method: 'POST'});
                    const data = await response.json();
                    
                    if (data.success) {
                        showAlert('warning', 'Voltage ramp stopped');
                        document.getElementById('startRampBtn').disabled = false;
                        document.getElementById('stopRampBtn').disabled = true;
                        document.getElementById('rampingStatus').className = 'status-indicator disconnected';
                    } else {
                        showAlert('danger', 'Stop ramp failed: ' + data.error);
                    }
                } catch (error) {
                    console.error('Stop ramp error:', error);
                    showAlert('danger', 'Stop ramp error: ' + error.message);
                }
            }
            
            // Update status from server
            async function updateStatus() {
                try {
                    const response = await fetch('/status');
                    const status = await response.json();
                    
                    // Update display values
                    document.getElementById('displaySetVoltage').textContent = status.set_voltage.toFixed(1) + ' V';
                    document.getElementById('displayActualVoltage').textContent = status.actual_voltage.toFixed(1) + ' V';
                    document.getElementById('displayCurrent').textContent = (status.current * 1000).toFixed(3) + ' mA';
                    document.getElementById('displayOutputStatus').textContent = status.output_enabled ? 'ON' : 'OFF';
                    document.getElementById('displayOutputStatus').style.color = status.output_enabled ? '#28a745' : '#dc3545';
                    document.getElementById('displayConnection').textContent = status.connected ? 'Connected' : 'Disconnected';
                    document.getElementById('displayConnection').style.color = status.connected ? '#28a745' : '#dc3545';
                    
                    // Update Start Voltage in ramp controls to match current Set Voltage
                    const newStartVoltage = status.set_voltage.toFixed(1);
                    const oldStartVoltage = document.getElementById('rampStart').value;
                    
                    // Only update DOM and trigger ramp info update if value changed
                    if (oldStartVoltage !== newStartVoltage) {
                        document.getElementById('rampStart').value = newStartVoltage;
                        updateRampInfo();
                    }
                    
                    // Store real voltage data point for interpolation (every 500ms)
                    const now = Date.now() / 1000; // Convert to seconds
                    
                    // Shift the voltage tracking for interpolation
                    lastRealVoltage = currentRealVoltage;
                    lastRealTimestamp = currentRealTimestamp;
                    currentRealVoltage = status.actual_voltage;
                    currentRealTimestamp = now;
                    
                    // Update connection state
                    updateConnectionState(status.connected);
                    
                    // Update ramp progress
                    if (status.ramping) {
                        document.getElementById('rampProgress').classList.add('show');
                        document.getElementById('rampProgressFill').style.width = status.ramp_progress + '%';
                        document.getElementById('rampProgressFill').textContent = Math.round(status.ramp_progress) + '%';
                        document.getElementById('startRampBtn').disabled = true;
                        document.getElementById('stopRampBtn').disabled = false;
                        document.getElementById('rampingStatus').className = 'status-indicator ramping';
                    } else {
                        document.getElementById('rampProgress').classList.remove('show');
                        // Re-validate ramp inputs since ramping stopped and button state needs updating based on current input validity and connection status
                        validateRampInputs();
                        document.getElementById('stopRampBtn').disabled = true;
                        document.getElementById('rampingStatus').className = 'status-indicator disconnected';
                    }
                    
                    // Show error if present
                    if (status.error) {
                        showAlert('danger', 'Error: ' + status.error);
                    }
                    
                } catch (error) {
                    console.error('Status update error:', error);
                }
            }
            
            // Update connection state UI
            function updateConnectionState(connected) {
                // Update modal status indicator
                document.getElementById('connectionStatus').className = 
                    'status-indicator ' + (connected ? 'connected' : 'disconnected');
                
                // Update toolbar status
                document.getElementById('toolbarConnectionStatus').className = 
                    'status-indicator ' + (connected ? 'connected' : 'disconnected');
                
                // Update toolbar text
                const toolbarText = document.getElementById('toolbarConnectionText');
                if (connected) {
                    const address = document.getElementById('visaAddress').value;
                    toolbarText.textContent = address ? `Connected: ${address.substring(0, 20)}...` : 'Connected';
                } else {
                    toolbarText.textContent = 'Disconnected';
                }
                
                document.getElementById('connectBtn').disabled = connected;
                document.getElementById('disconnectBtn').disabled = !connected;
                document.getElementById('outputOnBtn').disabled = !connected;
                document.getElementById('outputOffBtn').disabled = !connected;
                
                // Re-validate ramp inputs to update Start Ramp button state
                validateRampInputs();
                
                // Re-validate inputs to update button states
                validateSetVoltageInput();
                validateCurrentLimitInput();
            }
            
            // Start periodic status updates
            function startStatusUpdates() {
                updateStatus();  // Initial update
                updateInterval = setInterval(updateStatus, 500);  // Update every 500ms to match backend polling
            }
            
            // Stop status updates
            function stopStatusUpdates() {
                if (updateInterval) {
                    clearInterval(updateInterval);
                    updateInterval = null;
                }
            }
            
            // Start smooth animation loop (50ms updates)
            function startSmoothAnimation() {
                let lastAnimationTime = Date.now();
                let lastAddedTime = 0; // Track last time we added a point to avoid duplicates
                
                function animate() {
                    const currentAnimationTime = Date.now();
                    const now = currentAnimationTime / 1000; // Convert to seconds
                    
                    // Ensure we maintain approximately 50ms intervals
                    const elapsed = currentAnimationTime - lastAnimationTime;
                    if (elapsed >= 50) {
                        lastAnimationTime = currentAnimationTime;
                        
                        // Interpolate voltage between last two real data points
                        if (lastRealVoltage !== null && currentRealVoltage !== null && 
                            lastRealTimestamp !== null && currentRealTimestamp !== null) {
                            
                            const timeSinceLastReal = now - lastRealTimestamp;
                            const timeBetweenMeasurements = currentRealTimestamp - lastRealTimestamp;
                            
                            let shouldAddPoint = false;
                            let voltageToAdd = 0;
                            
                            // Guard against division by zero and invalid time ranges
                            if (timeBetweenMeasurements > 0 && timeSinceLastReal >= 0 && timeSinceLastReal <= timeBetweenMeasurements) {
                                // Calculate interpolation factor (0 to 1)
                                const t = timeSinceLastReal / timeBetweenMeasurements;
                                
                                // Linear interpolation between lastRealVoltage and currentRealVoltage
                                voltageToAdd = lastRealVoltage + (currentRealVoltage - lastRealVoltage) * t;
                                shouldAddPoint = true;
                            } else if (timeSinceLastReal > timeBetweenMeasurements && now - lastAddedTime >= 0.05) {
                                // We're past the current point, hold at current value
                                // Only add if at least 50ms since last point (avoid duplicates)
                                voltageToAdd = currentRealVoltage;
                                shouldAddPoint = true;
                            }
                            
                            if (shouldAddPoint) {
                                // Add point to history
                                voltageHistory.push({
                                    time: now,
                                    voltage: voltageToAdd
                                });
                                lastAddedTime = now;
                                
                                // Remove old data points outside the time window
                                // This prevents unbounded memory growth
                                const cutoffTime = now - scopeTimeWindow;
                                voltageHistory = voltageHistory.filter(point => point.time >= cutoffTime);
                                
                                // Update scope plot
                                drawScopePlot();
                            }
                        }
                    }
                    
                    // Schedule next animation frame
                    animationFrameId = requestAnimationFrame(animate);
                }
                
                // Start the animation loop
                animate();
            }
            
            // Stop smooth animation
            function stopSmoothAnimation() {
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                    animationFrameId = null;
                }
            }
            
            // Show alert message
            function showAlert(type, message) {
                // Show in modal alert if modal is open
                const modal = document.getElementById('connectionModal');
                if (modal && modal.classList.contains('show')) {
                    // Create temporary alert in modal if needed
                    const existingAlert = modal.querySelector('.alert');
                    if (!existingAlert) {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'alert alert-' + type + ' show';
                        alertDiv.textContent = message;
                        alertDiv.style.marginTop = '15px';
                        modal.appendChild(alertDiv);
                        
                        if (type !== 'danger') {
                            setTimeout(() => {
                                alertDiv.remove();
                            }, 5000);
                        }
                    }
                }
                
                // Always show in toolbar
                const alert = document.getElementById('toolbarAlertPanel');
                if (alert) {
                    alert.className = 'alert alert-' + type + ' show';
                    alert.textContent = message;
                    
                    // Auto-hide after 5 seconds for non-error messages
                    if (type !== 'danger') {
                        setTimeout(() => {
                            alert.classList.remove('show');
                        }, 5000);
                    }
                }
            }
            
            // Update ramp info and plot
            function updateRampInfo() {
                const start = parseFloat(document.getElementById('rampStart').value) || 0;
                const end = parseFloat(document.getElementById('rampEnd').value) || 0;
                const step = parseFloat(document.getElementById('rampStep').value) || 1;
                const delay = parseFloat(document.getElementById('rampDelay').value) || 1;
                
                const steps = Math.ceil(Math.abs(end - start) / step);
                const totalTime = steps * delay;
                
                document.getElementById('rampInfo').textContent = 
                    `${steps} steps, ~${totalTime.toFixed(1)}s total duration`;
                
                // Draw the ramp plot
                drawRampPlot(start, end, step, delay);
            }
            
            // Draw ramp plot on canvas
            function drawRampPlot(start, end, step, delay) {
                const canvas = document.getElementById('rampPlot');
                const ctx = canvas.getContext('2d');
                
                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Validate inputs
                if (step <= 0 || step > 1250) {
                    ctx.fillStyle = '#666';
                    ctx.font = '14px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText('Invalid step size', canvas.width / 2, canvas.height / 2);
                    return;
                }
                
                if (Math.abs(end - start) < 0.01) {
                    ctx.fillStyle = '#666';
                    ctx.font = '14px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText('Start and end voltages are too similar', canvas.width / 2, canvas.height / 2);
                    return;
                }
                
                // Set up dimensions with padding
                const padding = 40;
                const plotWidth = canvas.width - 2 * padding;
                const plotHeight = canvas.height - 2 * padding;
                
                // Calculate ramp points with safety limit
                const direction = end > start ? 1 : -1;
                const stepSigned = Math.abs(step) * direction;
                let voltage = start;
                const points = [];
                let currentTime = 0;
                const maxIterations = 10000; // Safety limit
                let iterations = 0;
                
                // Generate ramp points
                while (iterations < maxIterations) {
                    points.push({ time: currentTime, voltage: voltage });
                    
                    // Check if we've reached the end voltage
                    if ((direction > 0 && voltage >= end) || (direction < 0 && voltage <= end)) {
                        break;
                    }
                    
                    // Calculate next voltage
                    voltage += stepSigned;
                    
                    // Clamp to end voltage to prevent overshooting
                    if (direction < 0) {
                        voltage = Math.max(voltage, end);
                    } else {
                        voltage = Math.min(voltage, end);
                    }
                    
                    currentTime += delay;
                    iterations++;
                }
                
                // Find min/max for scaling
                const minVoltage = Math.min(start, end);
                const maxVoltage = Math.max(start, end);
                const maxTime = currentTime || 1; // Avoid division by zero, minimum 1 second
                
                // Y-axis starts at 0 (as requested) and extends to include all voltage values
                const voltageMin = 0;
                const voltageMax = Math.max(Math.abs(minVoltage), Math.abs(maxVoltage)) * 1.1; // 10% padding at top
                
                // Scale functions - x-axis autoscales to actual ramp duration, y-axis starts at 0
                const scaleX = (time) => padding + (time / maxTime) * plotWidth;
                const scaleY = (voltage) => padding + plotHeight - ((Math.abs(voltage) - voltageMin) / (voltageMax - voltageMin)) * plotHeight;
                
                // Draw grid
                ctx.strokeStyle = '#e9ecef';
                ctx.lineWidth = 1;
                
                // Horizontal grid lines (voltage) - y-axis starts at 0 and goes down (negative voltages)
                for (let i = 0; i <= 4; i++) {
                    const absV = voltageMin + (voltageMax - voltageMin) * i / 4;
                    const y = scaleY(-absV); // Use negative since we're showing negative voltages
                    ctx.beginPath();
                    ctx.moveTo(padding, y);
                    ctx.lineTo(canvas.width - padding, y);
                    ctx.stroke();
                    
                    // Label (show as negative voltage)
                    ctx.fillStyle = '#666';
                    ctx.font = '10px sans-serif';
                    ctx.textAlign = 'right';
                    ctx.fillText((-absV).toFixed(0) + 'V', padding - 5, y + 3);
                }
                
                // Vertical grid lines (time)
                for (let i = 0; i <= 4; i++) {
                    const t = maxTime * i / 4;
                    const x = scaleX(t);
                    ctx.beginPath();
                    ctx.moveTo(x, padding);
                    ctx.lineTo(x, canvas.height - padding);
                    ctx.stroke();
                    
                    // Label
                    ctx.fillStyle = '#666';
                    ctx.font = '10px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText(t.toFixed(1) + 's', x, canvas.height - padding + 15);
                }
                
                // Draw axes
                ctx.strokeStyle = '#333';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(padding, padding);
                ctx.lineTo(padding, canvas.height - padding);
                ctx.lineTo(canvas.width - padding, canvas.height - padding);
                ctx.stroke();
                
                // Draw ramp line and shaded area
                if (points.length > 0) {
                    // Draw shaded area above the curve (between curve and y=0 line)
                    ctx.fillStyle = 'rgba(102, 126, 234, 0.15)'; // Light blue with transparency
                    ctx.beginPath();
                    
                    // Start from the top-left (y=0 at first time point)
                    ctx.moveTo(scaleX(points[0].time), scaleY(0));
                    
                    // Draw along y=0 to the last time point
                    ctx.lineTo(scaleX(points[points.length - 1].time), scaleY(0));
                    
                    // Draw down to the last point on the curve
                    ctx.lineTo(scaleX(points[points.length - 1].time), scaleY(points[points.length - 1].voltage));
                    
                    // Draw back along the curve to the first point using step function
                    for (let i = points.length - 2; i >= 0; i--) {
                        // Draw horizontal line at current voltage level
                        ctx.lineTo(scaleX(points[i].time), scaleY(points[i + 1].voltage));
                        // Draw vertical line to next voltage level
                        ctx.lineTo(scaleX(points[i].time), scaleY(points[i].voltage));
                    }
                    
                    // Close the path back to the starting point
                    ctx.closePath();
                    ctx.fill();
                    
                    // Draw the ramp line itself using step function
                    ctx.strokeStyle = '#667eea';
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(scaleX(points[0].time), scaleY(points[0].voltage));
                    
                    for (let i = 1; i < points.length; i++) {
                        // Draw horizontal line at current voltage level
                        ctx.lineTo(scaleX(points[i].time), scaleY(points[i - 1].voltage));
                        // Draw vertical line to next voltage level
                        ctx.lineTo(scaleX(points[i].time), scaleY(points[i].voltage));
                    }
                    
                    ctx.stroke();
                    
                    // Draw points
                    ctx.fillStyle = '#667eea';
                    for (let i = 0; i < points.length; i++) {
                        ctx.beginPath();
                        ctx.arc(scaleX(points[i].time), scaleY(points[i].voltage), 3, 0, 2 * Math.PI);
                        ctx.fill();
                    }
                    
                    // Highlight start and end points
                    ctx.fillStyle = '#28a745';
                    ctx.beginPath();
                    ctx.arc(scaleX(points[0].time), scaleY(points[0].voltage), 5, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    ctx.fillStyle = '#dc3545';
                    ctx.beginPath();
                    ctx.arc(scaleX(points[points.length - 1].time), scaleY(points[points.length - 1].voltage), 5, 0, 2 * Math.PI);
                    ctx.fill();
                }
                
                // Axis labels removed for cleaner appearance
            }
            
            // Validate ramp input fields
            function validateRampInputs() {
                const endInput = document.getElementById('rampEnd');
                const startRampBtn = document.getElementById('startRampBtn');
                
                const endValue = parseFloat(endInput.value);
                
                let isValid = true;
                
                // Validate End Voltage: must be <= -50
                if (!isNaN(endValue) && endValue > -50) {
                    endInput.classList.add('invalid');
                    isValid = false;
                } else {
                    endInput.classList.remove('invalid');
                }
                
                // Disable Start Ramp button if End Voltage field is invalid or not connected
                const connected = isConnected();
                startRampBtn.disabled = !isValid || !connected;
            }
            
            // Validate Set Voltage input
            function validateSetVoltageInput() {
                const setVoltageInput = document.getElementById('setVoltage');
                const setVoltageBtn = document.getElementById('setVoltageBtn');
                
                const voltageValue = parseFloat(setVoltageInput.value);
                
                // Voltage range constants for PS310 (negative polarity model)
                const MIN_VOLTAGE = -1250;  // Maximum magnitude
                const MAX_VOLTAGE = -50;    // Minimum magnitude
                
                // Validate Set Voltage: must be between MIN_VOLTAGE and MAX_VOLTAGE (inclusive)
                const isValid = !isNaN(voltageValue) && voltageValue >= MIN_VOLTAGE && voltageValue <= MAX_VOLTAGE;
                
                if (isValid) {
                    setVoltageInput.classList.remove('invalid');
                } else {
                    setVoltageInput.classList.add('invalid');
                }
                
                // Disable Set Voltage button if field is invalid or not connected
                const connected = isConnected();
                setVoltageBtn.disabled = !isValid || !connected;
            }
            
            // Validate Current Limit input
            function validateCurrentLimitInput() {
                const currentLimitInput = document.getElementById('currentLimit');
                const setCurrentBtn = document.getElementById('setCurrentBtn');
                
                const currentValue = parseFloat(currentLimitInput.value);
                
                // Current limit range constants for PS310
                const MIN_CURRENT = 0;
                const MAX_CURRENT = 21;  // mA
                
                // Validate Current Limit: must be between MIN_CURRENT and MAX_CURRENT (inclusive)
                const isValid = !isNaN(currentValue) && currentValue >= MIN_CURRENT && currentValue <= MAX_CURRENT;
                
                if (isValid) {
                    currentLimitInput.classList.remove('invalid');
                } else {
                    currentLimitInput.classList.add('invalid');
                }
                
                // Disable Set Current button if field is invalid or not connected
                const connected = isConnected();
                setCurrentBtn.disabled = !isValid || !connected;
            }
            
            // Check if device is connected
            function isConnected() {
                return document.getElementById('connectionStatus').classList.contains('connected');
            }
            
            // Add event listeners for ramp parameter changes (rampStart updates via status polling, not user input)
            ['rampEnd', 'rampStep', 'rampDelay'].forEach(id => {
                document.getElementById(id).addEventListener('input', updateRampInfo);
            });
            
            // Add validation listener for rampEnd only (rampStart is read-only now)
            document.getElementById('rampEnd').addEventListener('input', validateRampInputs);
            
            // Add validation listeners for Set Voltage and Current Limit
            document.getElementById('setVoltage').addEventListener('input', validateSetVoltageInput);
            document.getElementById('currentLimit').addEventListener('input', validateCurrentLimitInput);
            
            // Initial ramp info update
            updateRampInfo();
            
            // Initial validation
            validateRampInputs();
            validateSetVoltageInput();
            validateCurrentLimitInput();
            
            // Toggle scope settings popover
            function toggleScopeSettings() {
                const popover = document.getElementById('scopeSettingsPopover');
                const backdrop = document.getElementById('modalBackdrop');
                popover.classList.toggle('show');
                backdrop.classList.toggle('show');
            }
            
            // Close scope settings popover
            function closeScopeSettings() {
                const popover = document.getElementById('scopeSettingsPopover');
                const backdrop = document.getElementById('modalBackdrop');
                popover.classList.remove('show');
                backdrop.classList.remove('show');
            }
            
            // Apply scope settings
            function applyScopeSettings() {
                const newWindow = parseInt(document.getElementById('scopeTimeWindow').value);
                if (newWindow >= 5 && newWindow <= 300) {
                    scopeTimeWindow = newWindow;
                    closeScopeSettings();
                    showAlert('success', `Time window updated to ${scopeTimeWindow} seconds`);
                    // Clear old data that's outside the new window
                    const now = Date.now() / 1000;
                    const cutoffTime = now - scopeTimeWindow;
                    voltageHistory = voltageHistory.filter(point => point.time >= cutoffTime);
                    drawScopePlot();
                } else {
                    showAlert('warning', 'Time window must be between 5 and 300 seconds');
                }
            }
            
            // Draw the scope plot
            function drawScopePlot() {
                const canvas = document.getElementById('scopePlot');
                const ctx = canvas.getContext('2d');
                
                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Set up dimensions with padding (smaller for compact view)
                const padding = 35;
                const plotWidth = canvas.width - 2 * padding;
                const plotHeight = canvas.height - 2 * padding;
                
                // If no data, show message
                if (voltageHistory.length === 0) {
                    ctx.fillStyle = '#ccc';
                    ctx.font = '11px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText('Waiting for data...', canvas.width / 2, canvas.height / 2);
                    return;
                }
                
                // Calculate time range - always show full window even if we don't have data
                const now = Date.now() / 1000;
                const minTime = now - scopeTimeWindow;
                const maxTime = now;
                
                // Find voltage range from data
                let minVoltage = 0;
                let maxVoltage = 0;
                if (voltageHistory.length > 0) {
                    minVoltage = Math.min(...voltageHistory.map(p => p.voltage));
                    maxVoltage = Math.max(...voltageHistory.map(p => p.voltage));
                    
                    // Add 10% padding to voltage range
                    const voltageRange = Math.abs(maxVoltage - minVoltage);
                    const padding_v = voltageRange * 0.1;
                    minVoltage -= padding_v;
                    maxVoltage += padding_v;
                    
                    // Ensure we have at least some range
                    if (Math.abs(maxVoltage - minVoltage) < 1) {
                        minVoltage -= 0.5;
                        maxVoltage += 0.5;
                    }
                }
                
                // Scale functions
                const scaleX = (time) => padding + ((time - minTime) / scopeTimeWindow) * plotWidth;
                const scaleY = (voltage) => {
                    const range = maxVoltage - minVoltage;
                    if (range === 0) return canvas.height / 2;
                    return padding + plotHeight - ((voltage - minVoltage) / range) * plotHeight;
                };
                
                // Draw grid
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
                ctx.lineWidth = 1;
                
                // Horizontal grid lines (voltage) - fewer lines for compact view
                for (let i = 0; i <= 3; i++) {
                    const v = minVoltage + (maxVoltage - minVoltage) * i / 3;
                    const y = scaleY(v);
                    ctx.beginPath();
                    ctx.moveTo(padding, y);
                    ctx.lineTo(canvas.width - padding, y);
                    ctx.stroke();
                    
                    // Label
                    ctx.fillStyle = '#ccc';
                    ctx.font = '9px sans-serif';
                    ctx.textAlign = 'right';
                    ctx.fillText(v.toFixed(1) + 'V', padding - 3, y + 3);
                }
                
                // Vertical grid lines (time) - fewer lines for compact view
                const numTimeLabels = 4;
                for (let i = 0; i <= numTimeLabels; i++) {
                    const t = minTime + (scopeTimeWindow * i / numTimeLabels);
                    const x = scaleX(t);
                    ctx.beginPath();
                    ctx.moveTo(x, padding);
                    ctx.lineTo(x, canvas.height - padding);
                    ctx.stroke();
                    
                    // Label (relative time in seconds from now)
                    ctx.fillStyle = '#ccc';
                    ctx.font = '9px sans-serif';
                    ctx.textAlign = 'center';
                    const relativeTime = -(now - t);
                    ctx.fillText(relativeTime.toFixed(0) + 's', x, canvas.height - padding + 12);
                }
                
                // Draw axes
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padding, padding);
                ctx.lineTo(padding, canvas.height - padding);
                ctx.lineTo(canvas.width - padding, canvas.height - padding);
                ctx.stroke();
                
                // Draw voltage trace
                if (voltageHistory.length > 0) {
                    // Draw filled area
                    ctx.fillStyle = 'rgba(102, 126, 234, 0.2)';
                    ctx.beginPath();
                    ctx.moveTo(scaleX(voltageHistory[0].time), canvas.height - padding);
                    
                    for (let i = 0; i < voltageHistory.length; i++) {
                        ctx.lineTo(scaleX(voltageHistory[i].time), scaleY(voltageHistory[i].voltage));
                    }
                    
                    ctx.lineTo(scaleX(voltageHistory[voltageHistory.length - 1].time), canvas.height - padding);
                    ctx.closePath();
                    ctx.fill();
                    
                    // Draw line
                    ctx.strokeStyle = '#66aaff';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(scaleX(voltageHistory[0].time), scaleY(voltageHistory[0].voltage));
                    
                    for (let i = 1; i < voltageHistory.length; i++) {
                        ctx.lineTo(scaleX(voltageHistory[i].time), scaleY(voltageHistory[i].voltage));
                    }
                    
                    ctx.stroke();
                    
                    // Draw latest point
                    const latest = voltageHistory[voltageHistory.length - 1];
                    ctx.fillStyle = '#66aaff';
                    ctx.beginPath();
                    ctx.arc(scaleX(latest.time), scaleY(latest.voltage), 3, 0, 2 * Math.PI);
                    ctx.fill();
                }
            }
            
            // Close popover when clicking outside or on backdrop
            document.addEventListener('click', function(event) {
                const scopePopover = document.getElementById('scopeSettingsPopover');
                const scopeSettingsBtn = document.getElementById('scopeSettingsBtn');
                
                if (scopePopover.classList.contains('show') && 
                    !scopePopover.contains(event.target) && 
                    !scopeSettingsBtn.contains(event.target)) {
                    closeScopeSettings();
                }
            });
            
            // Clean up on page unload
            window.addEventListener('beforeunload', function() {
                stopStatusUpdates();
                stopSmoothAnimation();
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/list_visa_resources")
async def list_visa_resources():
    """List available VISA resources using PyVISA ResourceManager."""
    if pyvisa is None:
        logger.error("PyVISA is not installed")
        return {"resources": [], "error": "PyVISA is not installed. Install it with: pip install pyvisa"}
    
    rm = None
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        logger.info(f"Found {len(resources)} VISA resources: {list(resources)}")
        return {"resources": list(resources)}
    except Exception as e:
        error_str = str(e)
        logger.error(f"Error listing VISA resources: {error_str}")
        
        if "VISA implementation" in error_str or "IVI binary" in error_str or "pyvisa-py" in error_str:
            error_msg = "Could not locate a VISA implementation. Install either the IVI binary or pyvisa-py."
        else:
            error_msg = "Could not scan for VISA devices. Check server logs for details."
        return {"resources": [], "error": error_msg}
    finally:
        if rm is not None:
            try:
                rm.close()
            except Exception as e:
                logger.warning(f"Error closing ResourceManager: {e}")

@app.post("/connect")
async def connect_device(request: Request):
    """Connect to the Stanford PS310 power supply."""
    global ps310_instance, ps310_state
    
    try:
        data = await request.json()
        address = data.get('address')
        
        if not address:
            return JSONResponse(content={"success": False, "error": "VISA address is required"})
        
        if StanfordPS310 is None:
            return JSONResponse(content={"success": False, "error": "StanfordPS310 driver not available"})
        
        # Create new instance and connect
        ps310_instance = StanfordPS310(auto_connect=False)
        ps310_instance.connect(address=address)
        
        # Update state
        ps310_state["connected"] = True
        ps310_state["address"] = address
        ps310_state["error"] = None
        
        # Read initial values through the queue
        try:
            set_voltage = await queue_command(
                ps310_instance.get_voltage,
                priority=CommandPriority.NORMAL
            )
            actual_voltage = await queue_command(
                ps310_instance.measure_voltage,
                priority=CommandPriority.NORMAL
            )
            current = await queue_command(
                ps310_instance.measure_current,
                priority=CommandPriority.NORMAL
            )
            output_state = await queue_command(
                ps310_instance.get_output_state,
                priority=CommandPriority.NORMAL
            )
            
            ps310_state["set_voltage"] = set_voltage
            ps310_state["actual_voltage"] = actual_voltage
            ps310_state["current"] = current
            ps310_state["output_enabled"] = output_state
        except Exception as e:
            logger.warning(f"Could not read initial values: {e}")
        
        logger.info(f"Successfully connected to PS310 at {address}")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Connection error: {error_msg}")
        ps310_state["connected"] = False
        ps310_state["error"] = error_msg
        return JSONResponse(content={"success": False, "error": error_msg})

@app.post("/disconnect")
async def disconnect_device():
    """Disconnect from the Stanford PS310 power supply."""
    global ps310_instance, ps310_state
    
    try:
        if ps310_instance:
            # Turn off output before disconnecting (high priority)
            try:
                await queue_command(
                    ps310_instance.set_output_state,
                    False,
                    priority=CommandPriority.HIGH
                )
            except Exception:
                pass
            
            ps310_instance.disconnect()
            ps310_instance = None
        
        ps310_state["connected"] = False
        ps310_state["address"] = None
        ps310_state["output_enabled"] = False
        ps310_state["error"] = None
        
        logger.info("Disconnected from PS310")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Disconnect error: {error_msg}")
        return JSONResponse(content={"success": False, "error": error_msg})

@app.post("/set_voltage")
async def set_voltage(request: Request):
    """Set the output voltage."""
    global ps310_instance, ps310_state
    
    try:
        if not ps310_instance or not ps310_state["connected"]:
            return JSONResponse(content={"success": False, "error": "Not connected to PS310"})
        
        data = await request.json()
        voltage = data.get('voltage')
        
        if voltage is None:
            return JSONResponse(content={"success": False, "error": "Voltage value is required"})
        
        # Queue the set_voltage command
        await queue_command(ps310_instance.set_voltage, voltage, priority=CommandPriority.NORMAL)
        ps310_state["set_voltage"] = voltage
        
        logger.info(f"Set voltage to {voltage}V")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Set voltage error: {error_msg}")
        return JSONResponse(content={"success": False, "error": error_msg})

@app.post("/set_current_limit")
async def set_current_limit(request: Request):
    """Set the current limit."""
    global ps310_instance, ps310_state
    
    try:
        if not ps310_instance or not ps310_state["connected"]:
            return JSONResponse(content={"success": False, "error": "Not connected to PS310"})
        
        data = await request.json()
        current = data.get('current')
        
        if current is None:
            return JSONResponse(content={"success": False, "error": "Current value is required"})
        
        # Queue the set_current_limit command
        await queue_command(ps310_instance.set_current_limit, current, priority=CommandPriority.NORMAL)
        
        logger.info(f"Set current limit to {current*1000}mA")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Set current limit error: {error_msg}")
        return JSONResponse(content={"success": False, "error": error_msg})

@app.post("/set_output")
async def set_output(request: Request):
    """Enable or disable the high voltage output."""
    global ps310_instance, ps310_state
    
    try:
        if not ps310_instance or not ps310_state["connected"]:
            return JSONResponse(content={"success": False, "error": "Not connected to PS310"})
        
        data = await request.json()
        state = data.get('state')
        
        if state is None:
            return JSONResponse(content={"success": False, "error": "State value is required"})
        
        # Queue the set_output_state command
        await queue_command(ps310_instance.set_output_state, state, priority=CommandPriority.NORMAL)
        ps310_state["output_enabled"] = state
        
        logger.info(f"Output {'enabled' if state else 'disabled'}")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Set output error: {error_msg}")
        return JSONResponse(content={"success": False, "error": error_msg})

@app.post("/start_ramp")
async def start_ramp(request: Request):
    """Start a voltage ramp."""
    global ps310_instance, ps310_state, ramp_task
    
    try:
        if not ps310_instance or not ps310_state["connected"]:
            return JSONResponse(content={"success": False, "error": "Not connected to PS310"})
        
        if ps310_state["ramping"]:
            return JSONResponse(content={"success": False, "error": "Ramp already in progress"})
        
        data = await request.json()
        start = data.get('start')
        end = data.get('end')
        step = data.get('step')
        delay = data.get('delay')
        
        if None in [start, end, step, delay]:
            return JSONResponse(content={"success": False, "error": "All ramp parameters are required"})
        
        # Start the ramp task
        ps310_state["ramping"] = True
        ps310_state["ramp_progress"] = 0
        ramp_task = asyncio.create_task(execute_ramp(start, end, step, delay))
        
        logger.info(f"Started voltage ramp: {start}V to {end}V, step {step}V, delay {delay}s")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Start ramp error: {error_msg}")
        ps310_state["ramping"] = False
        return JSONResponse(content={"success": False, "error": error_msg})

@app.post("/stop_ramp")
async def stop_ramp():
    """Stop the current voltage ramp."""
    global ps310_state, ramp_task
    
    try:
        if ramp_task and not ramp_task.done():
            ramp_task.cancel()
            try:
                await ramp_task
            except asyncio.CancelledError:
                pass
        
        ps310_state["ramping"] = False
        ps310_state["ramp_progress"] = 0
        
        logger.info("Stopped voltage ramp")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Stop ramp error: {error_msg}")
        return JSONResponse(content={"success": False, "error": error_msg})

async def execute_ramp(start: float, end: float, step: float, delay: float):
    """Execute the voltage ramp in the background."""
    global ps310_instance, ps310_state
    
    try:
        import math
        
        # Determine direction
        direction = 1 if end > start else -1
        step_signed = abs(step) * direction
        
        # Calculate total steps (use ceil to ensure we reach the end voltage)
        total_steps = math.ceil(abs(end - start) / abs(step)) + 1
        current_step = 0
        
        # Ramp loop
        voltage = start
        while True:
            try:
                # Queue the set voltage command
                await queue_command(
                    ps310_instance.set_voltage, 
                    voltage,
                    priority=CommandPriority.NORMAL
                )
                ps310_state["set_voltage"] = voltage
                
                # Update progress
                current_step += 1
                ps310_state["ramp_progress"] = (current_step / total_steps) * 100
                
                logger.info(f"Ramp step {current_step}/{total_steps}: {voltage}V")
                
                # Check if we've reached the end voltage
                if (direction > 0 and voltage >= end) or (direction < 0 and voltage <= end):
                    # We've reached the end voltage, stop the ramp
                    logger.info(f"Reached end voltage {end}V, stopping ramp")
                    break
                
                # Wait for next step
                await asyncio.sleep(delay)
                
                # Calculate next voltage
                voltage += step_signed
                
                # Ensure we don't overshoot
                if direction > 0:
                    voltage = min(voltage, end)
                else:
                    voltage = max(voltage, end)
                    
            except asyncio.CancelledError:
                logger.info("Ramp cancelled by user")
                raise
            except Exception as e:
                logger.error(f"Error during ramp: {e}")
                ps310_state["error"] = str(e)
                break
        
        # Ramp complete
        ps310_state["ramping"] = False
        ps310_state["ramp_progress"] = 100
        logger.info(f"Voltage ramp completed: final voltage {voltage}V")
        
    except asyncio.CancelledError:
        ps310_state["ramping"] = False
        ps310_state["ramp_progress"] = 0
        logger.info("Ramp task cancelled")
    except Exception as e:
        ps310_state["ramping"] = False
        ps310_state["error"] = str(e)
        logger.error(f"Ramp execution error: {e}")

@app.get("/status")
async def get_status():
    """Get the current status of the power supply."""
    global ps310_instance, ps310_state
    
    try:
        # Update current and output state if connected
        # These are less frequently needed than voltage, so we update them here
        if ps310_instance and ps310_state["connected"]:
            try:
                # Queue current and output state measurements at low priority
                current = await queue_command(
                    ps310_instance.measure_current,
                    priority=CommandPriority.LOW
                )
                output_state = await queue_command(
                    ps310_instance.get_output_state,
                    priority=CommandPriority.LOW
                )
                ps310_state["current"] = current
                ps310_state["output_enabled"] = output_state
            except Exception as e:
                logger.debug(f"Error reading measurements: {e}")
                # Keep using cached values if query fails
        
        return JSONResponse(content=ps310_state)
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return JSONResponse(content={
            "connected": False,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    
    # Security: Bind to localhost by default to prevent unauthorized network access
    # For network access, users should use SSH tunneling or set up proper authentication
    host = os.environ.get("PS310_GUI_HOST", "127.0.0.1")
    port = int(os.environ.get("PS310_GUI_PORT", "8082"))
    
    print("🚀 Starting Stanford PS310 Power Supply GUI...")
    print(f"🌐 Server address: http://{host}:{port}")
    if host == "127.0.0.1":
        print("🔒 Security: Bound to localhost only")
        print("   For remote access, use SSH tunneling or set PS310_GUI_HOST=0.0.0.0")
    else:
        print("⚠️  WARNING: Server exposed to network - ensure proper network security!")
    print("💡 Use Ctrl+C to stop the server")
    print("⚠️  HIGH VOLTAGE DEVICE - Use appropriate safety precautions!")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
