#!/usr/bin/env python3
"""
FastAPI GUI for Stanford Research Systems PS310 High Voltage Power Supply
Provides a web interface for controlling the PS310 with voltage ramping features.
"""

import sys
import os
from pathlib import Path

# Ensure the virtual environment is activated and used for subprocesses
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
if os.name == "nt":
    venv_python = os.path.join(venv_path, "Scripts", "python.exe")
else:
    venv_python = os.path.join(venv_path, "bin", "python3")

if os.path.exists(venv_python):
    sys.executable = venv_python
else:
    venv_python = sys.executable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import logging
import traceback
import time
from datetime import datetime
from typing import Optional, Dict, Any

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

# Ramping task reference
ramp_task: Optional[asyncio.Task] = None

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
            
            .form-group small {
                display: block;
                margin-top: 5px;
                color: #666;
                font-size: 0.9em;
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
            
            .btn-full {
                width: 100%;
            }
            
            .display-panel {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
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
                padding: 15px 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }
            
            .alert.show {
                display: block;
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
        <div class="container">
            <div class="header">
                <h1>⚡ Stanford PS310 High Voltage Power Supply</h1>
                <p>Precision High Voltage Control with Adjustable Ramping</p>
            </div>
            
            <div class="main-content">
                <!-- Left Column: Connection & Control -->
                <div>
                    <!-- Connection Panel -->
                    <div class="panel">
                        <h2>
                            <span id="connectionStatus" class="status-indicator disconnected"></span>
                            Connection
                        </h2>
                        
                        <div id="alertPanel" class="alert"></div>
                        
                        <div class="form-group">
                            <label for="visaAddress">VISA Address:</label>
                            <select id="visaAddress">
                                <option value="">Loading devices...</option>
                            </select>
                            <small>Select the GPIB address of the PS310</small>
                        </div>
                        
                        <div class="btn-group">
                            <button id="connectBtn" class="btn btn-success btn-full" onclick="connectDevice()">
                                🔌 Connect
                            </button>
                            <button id="disconnectBtn" class="btn btn-danger btn-full" onclick="disconnectDevice()" disabled>
                                🔌 Disconnect
                            </button>
                        </div>
                        
                        <div class="btn-group">
                            <button class="btn btn-secondary" onclick="refreshVisaDevices()">
                                🔄 Refresh Devices
                            </button>
                        </div>
                    </div>
                    
                    <!-- Safety Warning -->
                    <div class="safety-warning">
                        <h3>⚠️ High Voltage Safety Warning</h3>
                        <ul>
                            <li>Maximum voltage: ±1250V</li>
                            <li>Always disable output before connecting/disconnecting</li>
                            <li>Use appropriate safety equipment</li>
                            <li>Verify connections before enabling output</li>
                        </ul>
                    </div>
                    
                    <!-- Manual Control Panel -->
                    <div class="panel">
                        <h2>🎛️ Manual Control</h2>
                        
                        <div class="form-group">
                            <label for="setVoltage">Set Voltage (V):</label>
                            <input type="number" id="setVoltage" value="-100" step="0.1" min="-1250" max="0">
                            <small>Range: -1250V to 0V (negative polarity model)</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="currentLimit">Current Limit (mA):</label>
                            <input type="number" id="currentLimit" value="10" step="0.1" min="0" max="21">
                            <small>Range: 0 to 21 mA</small>
                        </div>
                        
                        <div class="btn-group">
                            <button id="setVoltageBtn" class="btn btn-primary btn-full" onclick="setVoltage()" disabled>
                                📝 Set Voltage
                            </button>
                        </div>
                        
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
                
                <!-- Right Column: Monitoring & Ramping -->
                <div>
                    <!-- Display Panel -->
                    <div class="panel">
                        <h2>📊 Live Readings</h2>
                        
                        <div class="display-panel">
                            <div class="display-label">Set Voltage</div>
                            <div class="display-value" id="displaySetVoltage">0.0 V</div>
                        </div>
                        
                        <div class="display-row">
                            <div class="display-small">
                                <div class="display-label">Actual Voltage</div>
                                <div class="display-value" id="displayActualVoltage">0.0 V</div>
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
                    
                    <!-- Voltage Ramping Panel -->
                    <div class="panel">
                        <h2>
                            <span id="rampingStatus" class="status-indicator disconnected"></span>
                            Voltage Ramping
                        </h2>
                        
                        <div class="ramp-controls">
                            <div class="form-group">
                                <label for="rampStart">Start Voltage (V):</label>
                                <input type="number" id="rampStart" value="0" step="0.1" min="-1250" max="0">
                            </div>
                            
                            <div class="form-group">
                                <label for="rampEnd">End Voltage (V):</label>
                                <input type="number" id="rampEnd" value="-500" step="0.1" min="-1250" max="0">
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
                        
                        <div class="progress-bar" id="rampProgress">
                            <div class="progress-fill" id="rampProgressFill" style="width: 0%">0%</div>
                        </div>
                        
                        <div class="btn-group">
                            <button id="startRampBtn" class="btn btn-primary" onclick="startRamp()" disabled>
                                🚀 Start Ramp
                            </button>
                            <button id="stopRampBtn" class="btn btn-danger" onclick="stopRamp()" disabled>
                                🛑 Stop Ramp
                            </button>
                        </div>
                        
                        <div class="form-group">
                            <small>
                                <strong>Ramp Info:</strong>
                                <span id="rampInfo">Configure ramp parameters above</span>
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let updateInterval = null;
            
            // Initialize the GUI
            window.addEventListener('load', function() {
                refreshVisaDevices();
                startStatusUpdates();
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
                const currentLimit = parseFloat(document.getElementById('currentLimit').value);
                
                if (isNaN(voltage) || voltage > 0 || voltage < -1250) {
                    showAlert('warning', 'Invalid voltage. Must be between -1250V and 0V');
                    return;
                }
                
                try {
                    // Set current limit first
                    if (!isNaN(currentLimit)) {
                        await fetch('/set_current_limit', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({current: currentLimit / 1000})  // Convert mA to A
                        });
                    }
                    
                    // Set voltage
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
                        document.getElementById('startRampBtn').disabled = !status.connected;
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
                document.getElementById('connectionStatus').className = 
                    'status-indicator ' + (connected ? 'connected' : 'disconnected');
                
                document.getElementById('connectBtn').disabled = connected;
                document.getElementById('disconnectBtn').disabled = !connected;
                document.getElementById('setVoltageBtn').disabled = !connected;
                document.getElementById('outputOnBtn').disabled = !connected;
                document.getElementById('outputOffBtn').disabled = !connected;
                document.getElementById('startRampBtn').disabled = !connected;
            }
            
            // Start periodic status updates
            function startStatusUpdates() {
                updateStatus();  // Initial update
                updateInterval = setInterval(updateStatus, 1000);  // Update every second
            }
            
            // Stop status updates
            function stopStatusUpdates() {
                if (updateInterval) {
                    clearInterval(updateInterval);
                    updateInterval = null;
                }
            }
            
            // Show alert message
            function showAlert(type, message) {
                const alert = document.getElementById('alertPanel');
                alert.className = 'alert alert-' + type + ' show';
                alert.textContent = message;
                
                // Auto-hide after 5 seconds for non-error messages
                if (type !== 'danger') {
                    setTimeout(() => {
                        alert.classList.remove('show');
                    }, 5000);
                }
            }
            
            // Update ramp info
            function updateRampInfo() {
                const start = parseFloat(document.getElementById('rampStart').value) || 0;
                const end = parseFloat(document.getElementById('rampEnd').value) || 0;
                const step = parseFloat(document.getElementById('rampStep').value) || 1;
                const delay = parseFloat(document.getElementById('rampDelay').value) || 1;
                
                const steps = Math.ceil(Math.abs(end - start) / step);
                const totalTime = steps * delay;
                
                document.getElementById('rampInfo').textContent = 
                    `${steps} steps, ~${totalTime.toFixed(1)}s total duration`;
            }
            
            // Add event listeners for ramp parameter changes
            ['rampStart', 'rampEnd', 'rampStep', 'rampDelay'].forEach(id => {
                document.getElementById(id).addEventListener('input', updateRampInfo);
            });
            
            // Initial ramp info update
            updateRampInfo();
            
            // Clean up on page unload
            window.addEventListener('beforeunload', function() {
                stopStatusUpdates();
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
        
        # Read initial values
        try:
            ps310_state["set_voltage"] = ps310_instance.get_voltage()
            ps310_state["actual_voltage"] = ps310_instance.measure_voltage()
            ps310_state["current"] = ps310_instance.measure_current()
            ps310_state["output_enabled"] = ps310_instance.get_output_state()
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
            # Turn off output before disconnecting
            try:
                ps310_instance.set_output_state(False)
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
        
        ps310_instance.set_voltage(voltage)
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
        
        ps310_instance.set_current_limit(current)
        
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
        
        ps310_instance.set_output_state(state)
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
        # Determine direction
        direction = 1 if end > start else -1
        step_signed = abs(step) * direction
        
        # Calculate total steps
        total_steps = int(abs(end - start) / abs(step)) + 1
        current_step = 0
        
        # Ramp loop
        voltage = start
        while (direction > 0 and voltage <= end) or (direction < 0 and voltage >= end):
            try:
                # Set voltage
                ps310_instance.set_voltage(voltage)
                ps310_state["set_voltage"] = voltage
                
                # Update progress
                current_step += 1
                ps310_state["ramp_progress"] = (current_step / total_steps) * 100
                
                logger.info(f"Ramp step {current_step}/{total_steps}: {voltage}V")
                
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
        # Update measurements if connected
        if ps310_instance and ps310_state["connected"]:
            try:
                ps310_state["actual_voltage"] = ps310_instance.measure_voltage()
                ps310_state["current"] = ps310_instance.measure_current()
                ps310_state["output_enabled"] = ps310_instance.get_output_state()
            except Exception as e:
                logger.error(f"Error reading measurements: {e}")
                ps310_state["error"] = str(e)
        
        return JSONResponse(content=ps310_state)
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return JSONResponse(content={
            "connected": False,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Stanford PS310 Power Supply GUI...")
    print("🌐 Open your browser to: http://localhost:8082")
    print("💡 Use Ctrl+C to stop the server")
    print("⚠️  HIGH VOLTAGE DEVICE - Use appropriate safety precautions!")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8082,
        log_level="info"
    )
