#!/usr/bin/env python3
"""
FastAPI GUI for Keysight MSOX4154A Oscilloscope Measurement Capture
Provides a web interface for configuring and running measurement tests.
"""

import sys
import os

# Ensure the virtual environment is activated and used for subprocesses
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
if os.name == "nt":
    venv_python = os.path.join(venv_path, "Scripts", "python.exe")
else:
    venv_python = os.path.join(venv_path, "bin", "python3")

if os.path.exists(venv_python):
    sys.executable = venv_python
else:
    # Fallback: use current sys.executable
    venv_python = sys.executable

from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json
import uvicorn
import logging
import traceback
import yaml
import shutil
import uuid
import mimetypes

app = FastAPI(title="Oscilloscope Measurement GUI", version="1.0.0")

# Create temp directory for images
temp_dir = Path("./.temp")
temp_dir.mkdir(exist_ok=True)

# Serve static files from temp directory
app.mount("/temp", StaticFiles(directory=".temp"), name="temp")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('measurement_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables to track test status
current_test_status = {"running": False, "progress": "", "error": None}
test_results = {"files": [], "measurements": []}

def load_defaults():
    """Load default configuration from defaults.yml file."""
    defaults_file = Path("defaults.yml")
    
    # Default fallback values
    defaults = {
        "visa_address": "USB0::0x0957::0x17BC::MY56310625::INSTR",
        "destination": "./captures",
        "board_number": "00001",
        "label": "Test",
        "channels": {
            "CH1": {"enabled": True, "label": "Channel 1", "color": "yellow"},
            "CH2": {"enabled": False, "label": "Channel 2", "color": "lime"},
            "CH3": {"enabled": False, "label": "Channel 3", "color": "cyan"},
            "CH4": {"enabled": False, "label": "Channel 4", "color": "magenta"},
            "M1": {"enabled": True, "label": "Math 1", "color": "#d6b4fc"}
        },
        "capture_types": {
            "measurements": True,
            "waveforms": True,
            "screenshot": True,
            "config": True,
            "html_report": True
        },
        "auto_timestamp": True,
        "timestamp_format": "YYYYMMDD.HHMMSS",
        "preview_output_path": True
    }
    
    if defaults_file.exists():
        try:
            # Try to import yaml, fallback to json if not available
            try:
                import yaml
                with open(defaults_file, 'r') as f:
                    loaded_defaults = yaml.safe_load(f) or {}
                    # Normalize channel structure for backward compatibility
                    if loaded_defaults.get("channels"):
                        normalized_channels = {}
                        for channel, config in loaded_defaults["channels"].items():
                            if isinstance(config, bool):
                                # Old format: just boolean enabled state
                                normalized_channels[channel] = {
                                    "enabled": config,
                                    "label": defaults["channels"][channel]["label"],
                                    "color": defaults["channels"][channel]["color"]
                                }
                            elif isinstance(config, dict):
                                # New format: full config object
                                normalized_channels[channel] = config
                            else:
                                # Fallback to defaults
                                normalized_channels[channel] = defaults["channels"][channel]
                        loaded_defaults["channels"] = normalized_channels
                    
                    defaults.update(loaded_defaults)
            except ImportError:
                logger.warning("PyYAML not installed, using fallback defaults")
        except Exception as e:
            logger.error(f"Error loading defaults.yml: {e}")
    else:
        logger.info("defaults.yml not found, using built-in defaults")
    
    return defaults

def generate_output_path(destination: str, board_number: str, label: str) -> str:
    """Generate parameterized output path: <destination>/Board_#####/B#####-YYYYMMDD.HHMMSS-<label>"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d.%H%M%S")
    
    # Handle board number formatting, preserving "00000" as special case
    if board_number == "00000":
        board_num_formatted = "00000"
    else:
        # Ensure board number is 5 digits with leading zeros
        board_num_formatted = f"{int(board_number):05d}"
    
    # Create the path components
    board_dir = f"Board_{board_num_formatted}"
    session_dir = f"B{board_num_formatted}-{timestamp}-{label}"
    
    # Combine into full path
    full_path = Path(destination) / board_dir / session_dir
    
    return str(full_path)

@app.get("/", response_class=HTMLResponse)
async def measurement_gui():
    """Main measurement configuration GUI."""
    # Load defaults for the form
    defaults = load_defaults()
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Oscilloscope Measurement GUI</title>
        
        <!-- CodeMirror CSS -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/default.min.css">
        
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #667eea;
            }
            .header h1 {
                color: #333;
                margin: 0;
                font-size: 2.5em;
            }
            .header p {
                color: #666;
                margin: 10px 0 0 0;
                font-size: 1.1em;
            }
            .form-section {
                margin: 25px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .form-section h3 {
                margin: 0 0 15px 0;
                color: #333;
                font-size: 1.3em;
            }
            .form-group {
                margin: 15px 0;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #555;
            }
            .form-group input[type="text"], .form-group select {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            .form-group input[type="text"]:focus, .form-group select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .checkbox-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 10px;
            }
            .checkbox-item {
                display: flex;
                align-items: center;
                padding: 10px;
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .checkbox-item:hover {
                border-color: #667eea;
                background: #f8f9ff;
            }
            .checkbox-item input[type="checkbox"] {
                margin-right: 10px;
                transform: scale(1.2);
            }
            .checkbox-item label {
                margin: 0;
                cursor: pointer;
                font-weight: 500;
            }
            .channel-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 15px;
            }
            .channel-item {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 15px;
                transition: all 0.3s;
            }
            .channel-item:hover {
                border-color: #667eea;
                background: #f8f9ff;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .channel-header {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
                gap: 10px;
            }
            .channel-checkbox-label {
                flex: 1;
                margin: 0;
                cursor: pointer;
                font-weight: 600;
                font-size: 14px;
            }
            .color-indicator {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 2px solid #333;
                flex-shrink: 0;
            }
            .channel-label-input {
                margin-top: 8px;
            }
            .label-input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                transition: all 0.3s;
            }
            .label-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
            }
            .channel-item input[type="checkbox"] {
                transform: scale(1.3);
                margin-right: 8px;
            }
            .button-group {
                text-align: center;
                margin: 30px 0;
            }
            .btn {
                padding: 12px 30px;
                margin: 0 10px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                display: inline-block;
            }
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            .btn-secondary:hover {
                background: #5a6268;
                transform: translateY(-2px);
            }
            .status-panel {
                margin: 20px 0;
                padding: 15px;
                border-radius: 8px;
                display: none;
            }
            .status-running {
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
            }
            .status-success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            .status-error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .results-panel {
                margin: 20px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                display: none;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: inline-block;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .pre-configured {
                font-size: 0.9em;
                color: #666;
                font-style: italic;
            }
            
            /* Image Upload and Management Styles */
            .image-upload-section {
                margin: 10px 0;
            }
            
            .upload-status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
                display: none;
            }
            
            .upload-status.success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                display: block;
            }
            
            .upload-status.error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                display: block;
            }
            
            .image-list {
                margin: 15px 0;
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background: white;
            }
            
            .image-item {
                display: flex;
                align-items: center;
                padding: 10px;
                border-bottom: 1px solid #e9ecef;
                transition: background-color 0.2s;
            }
            
            .image-item:last-child {
                border-bottom: none;
            }
            
            .image-item:hover {
                background-color: #f8f9fa;
            }
            
            .image-filename {
                flex: 1;
                margin-right: 10px;
                cursor: pointer;
                color: #667eea;
                text-decoration: underline;
                font-family: monospace;
                font-size: 14px;
            }
            
            .image-filename:hover {
                color: #764ba2;
            }
            
            .image-actions {
                display: flex;
                gap: 5px;
            }
            
            .image-btn {
                background: none;
                border: none;
                cursor: pointer;
                padding: 5px;
                border-radius: 3px;
                transition: background-color 0.2s;
                font-size: 16px;
            }
            
            .image-btn:hover {
                background-color: #e9ecef;
            }
            
            .image-btn.delete {
                color: #dc3545;
            }
            
            .image-btn.copy {
                color: #28a745;
            }
            
            /* Image Overlay */
            .image-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }
            
            .image-overlay-content {
                position: relative;
                max-width: 90%;
                max-height: 90%;
            }
            
            .image-overlay img {
                max-width: 100%;
                max-height: 100%;
                border-radius: 8px;
            }
            
            .image-overlay-close {
                position: absolute;
                top: -40px;
                right: 0;
                background: none;
                border: none;
                color: white;
                font-size: 30px;
                cursor: pointer;
            }
            
            /* CodeMirror Editor Styles */
            .CodeMirror {
                border: 1px solid #ddd;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                height: 300px;
            }
            
            .CodeMirror-focused {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 Oscilloscope Measurement GUI</h1>
                <p>Keysight MSOX4154A Configuration & Capture Interface</p>
            </div>

            <form id="measurementForm">
                <!-- Connection Settings -->
                <div class="form-section">
                    <h3>📡 Connection Settings</h3>
                    <div class="form-group">
                        <label for="visa_address">VISA Address:</label>
                        <input type="text" id="visa_address" name="visa_address" 
                               value="" 
                               placeholder="USB0::0x0957::0x17BC::MY56310625::INSTR">
                    </div>
                </div>

                <!-- Output Configuration -->
                <div class="form-section">
                    <h3>📁 Output Configuration</h3>
                    <div class="form-group">
                        <label for="destination">Base Destination:</label>
                        <input type="text" id="destination" name="destination" 
                               value="./captures" 
                               placeholder="./captures">
                        <small class="pre-configured">Base directory for all measurements</small>
                    </div>
                    <div class="form-group">
                        <label for="board_number">Board Number:</label>
                        <input type="text" id="board_number" name="board_number" 
                               value="00001" 
                               placeholder="00001"
                               pattern="[0-9]{1,5}"
                               title="Enter 1-5 digit board number">
                        <small class="pre-configured">Will be formatted as 5-digit number (e.g., 00001)</small>
                    </div>
                    <div class="form-group">
                        <label for="label">Measurement Label:</label>
                        <input type="text" id="label" name="label" 
                               value="Test" 
                               placeholder="Test_Name">
                        <small class="pre-configured">Descriptive label for this measurement session</small>
                    </div>
                    <div class="form-group">
                        <label>Generated Output Path:</label>
                        <div id="output_path_preview" style="padding: 10px; background: #e9ecef; border-radius: 5px; font-family: monospace; font-size: 14px; color: #495057;">
                            ./captures/Board_00001/B00001-YYYYMMDD.HHMMSS-Test/
                        </div>
                        <small class="pre-configured">Files will be saved in this auto-generated directory</small>
                    </div>
                </div>

                <!-- Channel Selection -->
                <div class="form-section">
                    <h3>📊 Channel Selection & Labels</h3>
                    <div class="channel-grid">
                        <div class="channel-item" data-channel="CH1">
                            <div class="channel-header">
                                <input type="checkbox" id="ch1" name="channels" value="CH1" checked>
                                <label for="ch1" class="channel-checkbox-label">CH1 - Analog Channel 1</label>
                                <div class="color-indicator" style="background-color: yellow;"></div>
                            </div>
                            <div class="channel-label-input">
                                <input type="text" id="ch1_label" name="ch1_label" placeholder="Channel 1" class="label-input">
                            </div>
                        </div>
                        <div class="channel-item" data-channel="CH2">
                            <div class="channel-header">
                                <input type="checkbox" id="ch2" name="channels" value="CH2">
                                <label for="ch2" class="channel-checkbox-label">CH2 - Analog Channel 2</label>
                                <div class="color-indicator" style="background-color: lime;"></div>
                            </div>
                            <div class="channel-label-input">
                                <input type="text" id="ch2_label" name="ch2_label" placeholder="Channel 2" class="label-input">
                            </div>
                        </div>
                        <div class="channel-item" data-channel="CH3">
                            <div class="channel-header">
                                <input type="checkbox" id="ch3" name="channels" value="CH3">
                                <label for="ch3" class="channel-checkbox-label">CH3 - Analog Channel 3</label>
                                <div class="color-indicator" style="background-color: cyan;"></div>
                            </div>
                            <div class="channel-label-input">
                                <input type="text" id="ch3_label" name="ch3_label" placeholder="Channel 3" class="label-input">
                            </div>
                        </div>
                        <div class="channel-item" data-channel="CH4">
                            <div class="channel-header">
                                <input type="checkbox" id="ch4" name="channels" value="CH4">
                                <label for="ch4" class="channel-checkbox-label">CH4 - Analog Channel 4</label>
                                <div class="color-indicator" style="background-color: magenta;"></div>
                            </div>
                            <div class="channel-label-input">
                                <input type="text" id="ch4_label" name="ch4_label" placeholder="Channel 4" class="label-input">
                            </div>
                        </div>
                        <div class="channel-item" data-channel="M1">
                            <div class="channel-header">
                                <input type="checkbox" id="m1" name="channels" value="M1" checked>
                                <label for="m1" class="channel-checkbox-label">M1 - Math Channel 1</label>
                                <div class="color-indicator" style="background-color: #d6b4fc;"></div>
                            </div>
                            <div class="channel-label-input">
                                <input type="text" id="m1_label" name="m1_label" placeholder="Math 1" class="label-input">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Data Capture Options -->
                <div class="form-section">
                    <h3>💾 Data Capture Options</h3>
                    <div class="checkbox-grid">
                        <div class="checkbox-item">
                            <input type="checkbox" id="measurements" name="capture_types" value="measurements" checked>
                            <label for="measurements">📈 Measurement Results</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="waveforms" name="capture_types" value="waveforms" checked>
                            <label for="waveforms">〰️ Waveform Data (CSV)</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="screenshot" name="capture_types" value="screenshot" checked>
                            <label for="screenshot">📸 Screenshot</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="config" name="capture_types" value="config" checked>
                            <label for="config">⚙️ Oscilloscope Config</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="html_report" name="capture_types" value="html_report" checked>
                            <label for="html_report">📄 HTML Report</label>
                        </div>
                    </div>
                </div>

                <!-- Notes and Images Section -->
                <div class="form-section">
                    <h3>📝 Notes & Images</h3>
                    
                    <!-- Image Upload -->
                    <div class="form-group">
                        <label>📷 Upload Images:</label>
                        <div class="image-upload-section">
                            <input type="file" id="imageUpload" multiple accept="image/*" style="display: none;">
                            <button type="button" class="btn btn-secondary" onclick="document.getElementById('imageUpload').click()">
                                📁 Choose Images
                            </button>
                            <div id="uploadStatus" class="upload-status"></div>
                        </div>
                        
                        <!-- Image List -->
                        <div id="imageList" class="image-list">
                            <!-- Uploaded images will appear here -->
                        </div>
                    </div>
                    
                    <!-- Notes Editor -->
                    <div class="form-group">
                        <label for="notes">✍️ Measurement Notes (Markdown):</label>
                        <div id="notesEditor" style="height: 300px; border: 1px solid #ddd; border-radius: 8px;"></div>
                        <textarea id="notes" name="notes" style="display: none;" placeholder="Add your measurement notes here..."></textarea>
                        <small class="pre-configured">Use Markdown syntax for formatting. Upload images above and reference them with the provided markdown syntax.</small>
                    </div>
                </div>

                <!-- Control Buttons -->
                <div class="button-group">
                    <button type="submit" class="btn btn-primary" id="startTest">
                        🚀 Start Measurement
                    </button>
                    <button type="button" class="btn btn-secondary" id="clearForm">
                        🧹 Clear Form
                    </button>
                </div>
            </form>

            <!-- Status Panel -->
            <div id="statusPanel" class="status-panel">
                <div id="statusContent"></div>
            </div>

            <!-- Results Panel -->
            <div id="resultsPanel" class="results-panel">
                <h3>📊 Test Results</h3>
                <div id="resultsContent"></div>
            </div>
            
            <!-- Debug Panel -->
            <div id="debugPanel" class="results-panel">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3>🐛 Debug Information</h3>
                    <button type="button" class="btn btn-secondary" onclick="toggleDebugPanel()" id="debugToggle">
                        Show Debug
                    </button>
                </div>
                <div id="debugContent" style="display: none;">
                    <h4>Client Logs:</h4>
                    <div id="clientLogs" style="max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px;"></div>
                    
                    <h4 style="margin-top: 20px;">Server Status:</h4>
                    <div id="serverStatus" style="background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px;"></div>
                    
                    <button type="button" class="btn btn-secondary" onclick="fetchServerLogs()" style="margin-top: 10px;">
                        Refresh Server Logs
                    </button>
                </div>
            </div>
        </div>

        <!-- Image Overlay -->
        <div id="imageOverlay" class="image-overlay" onclick="closeImageOverlay()">
            <div class="image-overlay-content">
                <button class="image-overlay-close" onclick="closeImageOverlay()">&times;</button>
                <img id="overlayImage" src="" alt="Image Preview">
            </div>
        </div>

        <!-- CodeMirror JavaScript -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/markdown/markdown.min.js"></script>
        
        <script>
            // Initialize CodeMirror editor
            let notesEditor;
            document.addEventListener('DOMContentLoaded', function() {
                notesEditor = CodeMirror(document.getElementById('notesEditor'), {
                    mode: 'markdown',
                    lineNumbers: true,
                    theme: 'default',
                    lineWrapping: true,
                    placeholder: 'Add your measurement notes here using Markdown syntax...'
                });
                
                // Sync with hidden textarea
                notesEditor.on('change', function() {
                    document.getElementById('notes').value = notesEditor.getValue();
                });
                
                // Initialize image upload handler
                document.getElementById('imageUpload').addEventListener('change', handleImageUpload);
                
                // Load existing images on page load
                loadUploadedImages();
            });
            
            // Image handling functions
            async function handleImageUpload(event) {
                const files = event.target.files;
                if (!files.length) return;
                
                const uploadStatus = document.getElementById('uploadStatus');
                uploadStatus.className = 'upload-status';
                uploadStatus.textContent = 'Uploading images...';
                uploadStatus.style.display = 'block';
                
                try {
                    for (let file of files) {
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        const response = await fetch('/upload_image', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error(`Failed to upload ${file.name}`);
                        }
                    }
                    
                    uploadStatus.className = 'upload-status success';
                    uploadStatus.textContent = `Successfully uploaded ${files.length} image(s)`;
                    
                    // Refresh image list
                    loadUploadedImages();
                    
                    // Clear file input
                    event.target.value = '';
                    
                } catch (error) {
                    uploadStatus.className = 'upload-status error';
                    uploadStatus.textContent = `Error: ${error.message}`;
                    logMessage('ERROR', `Image upload failed: ${error.message}`);
                }
            }
            
            async function loadUploadedImages() {
                try {
                    const response = await fetch('/list_images');
                    const images = await response.json();
                    
                    const imageList = document.getElementById('imageList');
                    imageList.innerHTML = '';
                    
                    if (images.length === 0) {
                        imageList.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No images uploaded yet</div>';
                        return;
                    }
                    
                    images.forEach(image => {
                        const imageItem = document.createElement('div');
                        imageItem.className = 'image-item';
                        
                        imageItem.innerHTML = `
                            <span class="image-filename" onclick="previewImage('${image}')">${image}</span>
                            <div class="image-actions">
                                <button class="image-btn copy" onclick="copyMarkdownSyntax('${image}')" title="Copy Markdown syntax">
                                    📋
                                </button>
                                <button class="image-btn delete" onclick="deleteImage('${image}')" title="Delete image">
                                    🗑️
                                </button>
                            </div>
                        `;
                        
                        imageList.appendChild(imageItem);
                    });
                    
                } catch (error) {
                    logMessage('ERROR', `Failed to load images: ${error.message}`);
                }
            }
            
            function previewImage(filename) {
                const overlay = document.getElementById('imageOverlay');
                const overlayImage = document.getElementById('overlayImage');
                overlayImage.src = `/temp/${filename}`;
                overlay.style.display = 'flex';
            }
            
            function closeImageOverlay() {
                document.getElementById('imageOverlay').style.display = 'none';
            }
            
            async function copyMarkdownSyntax(filename) {
                const markdownSyntax = `![${filename}](/temp/${filename})`;
                
                try {
                    await navigator.clipboard.writeText(markdownSyntax);
                    
                    // Show temporary success feedback
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '✓';
                    button.style.color = '#28a745';
                    
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.color = '';
                    }, 1500);
                    
                } catch (error) {
                    logMessage('ERROR', `Failed to copy to clipboard: ${error.message}`);
                    // Fallback: show the syntax in an alert
                    alert(`Copy this Markdown syntax:\\n${markdownSyntax}`);
                }
            }
            
            async function deleteImage(filename) {
                if (!confirm(`Are you sure you want to delete ${filename}?`)) {
                    return;
                }
                
                try {
                    const response = await fetch(`/delete_image/${filename}`, {
                        method: 'DELETE'
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Failed to delete ${filename}`);
                    }
                    
                    // Refresh image list
                    loadUploadedImages();
                    
                } catch (error) {
                    logMessage('ERROR', `Failed to delete image: ${error.message}`);
                    alert(`Error deleting image: ${error.message}`);
                }
            }
            
            // Client-side logging
            const clientLogs = [];
            function logMessage(level, message) {
                const timestamp = new Date().toISOString();
                const logEntry = `[${timestamp}] ${level}: ${message}`;
                console.log(logEntry);
                
                // Store in client logs
                clientLogs.push(logEntry);
                if (clientLogs.length > 100) {
                    clientLogs.shift(); // Keep only last 100 entries
                }
                
                // Update debug panel if visible
                updateDebugPanel();
            }
            
            function toggleDebugPanel() {
                const content = document.getElementById('debugContent');
                const toggle = document.getElementById('debugToggle');
                
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    toggle.textContent = 'Hide Debug';
                    updateDebugPanel();
                } else {
                    content.style.display = 'none';
                    toggle.textContent = 'Show Debug';
                }
            }
            
            function updateDebugPanel() {
                const clientLogsDiv = document.getElementById('clientLogs');
                const serverStatusDiv = document.getElementById('serverStatus');
                
                if (clientLogsDiv && clientLogs.length > 0) {
                    clientLogsDiv.innerHTML = clientLogs.slice(-20).join('<br>'); // Show last 20 entries
                    clientLogsDiv.scrollTop = clientLogsDiv.scrollHeight;
                }
                
                if (serverStatusDiv) {
                    serverStatusDiv.innerHTML = `
                        <strong>Current Status:</strong> ${JSON.stringify(window.lastStatus || {}, null, 2)}<br>
                        <strong>Last Update:</strong> ${new Date().toISOString()}
                    `;
                }
            }
            
            document.getElementById('measurementForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                logMessage('INFO', 'Form submission started');
                
                const formData = new FormData(this);
                
                // Collect channel data with labels
                const selectedChannels = formData.getAll('channels');
                const channelData = {};
                selectedChannels.forEach(channel => {
                    const labelInput = document.getElementById(channel.toLowerCase() + '_label');
                    channelData[channel] = {
                        enabled: true,
                        label: labelInput ? labelInput.value || `${channel} Default` : `${channel} Default`
                    };
                });
                
                const data = {
                    visa_address: formData.get('visa_address'),
                    destination: formData.get('destination'),
                    board_number: formData.get('board_number'),
                    label: formData.get('label'),
                    channels: selectedChannels,
                    channel_labels: channelData,
                    capture_types: formData.getAll('capture_types'),
                    notes: notesEditor ? notesEditor.getValue() : formData.get('notes')
                };
                
                logMessage('INFO', `Form data: ${JSON.stringify(data)}`);
                
                // Validate data
                if (!data.visa_address || data.visa_address.trim() === '') {
                    logMessage('ERROR', 'VISA address is empty');
                    showStatus('error', '❌ Error: VISA address is required');
                    return;
                }
                
                if (!data.destination || data.destination.trim() === '') {
                    logMessage('ERROR', 'Destination directory is empty');
                    showStatus('error', '❌ Error: Destination directory is required');
                    return;
                }
                
                if (!data.board_number || data.board_number.trim() === '') {
                    logMessage('ERROR', 'Board number is empty');
                    showStatus('error', '❌ Error: Board number is required');
                    return;
                }
                
                if (!data.label || data.label.trim() === '') {
                    logMessage('ERROR', 'Label is empty');
                    showStatus('error', '❌ Error: Measurement label is required');
                    return;
                }
                
                // Show running status
                showStatus('running', '<div class="spinner"></div>Starting measurement capture...');
                document.getElementById('startTest').disabled = true;
                
                try {
                    logMessage('INFO', 'Sending POST request to /start_measurement');
                    
                    const response = await fetch('/start_measurement', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    logMessage('INFO', `Response status: ${response.status} ${response.statusText}`);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const result = await response.json();
                    logMessage('INFO', `Response data: ${JSON.stringify(result)}`);
                    
                    if (result.success) {
                        logMessage('INFO', 'Measurement started, beginning status polling');
                        // Poll for status updates
                        pollStatus();
                    } else {
                        logMessage('ERROR', `Server returned error: ${result.error}`);
                        showStatus('error', `❌ Error: ${result.error}`);
                        document.getElementById('startTest').disabled = false;
                    }
                } catch (error) {
                    logMessage('ERROR', `Fetch error: ${error.message}`);
                    console.error('Full error object:', error);
                    
                    let errorMessage = `Connection Error: ${error.message}`;
                    if (error.name === 'TypeError' && error.message.includes('fetch')) {
                        errorMessage += '\\n\\nPossible causes:\\n- Server not running\\n- Wrong port (should be 8081)\\n- Network connectivity issues';
                    }
                    
                    showStatus('error', `❌ ${errorMessage}`);
                    document.getElementById('startTest').disabled = false;
                    
                    // Show debug panel automatically on error
                    showDebugOnError();
                    
                    // Try to get server logs
                    setTimeout(() => {
                        fetchServerLogs();
                    }, 1000);
                }
            });
            
            async function pollStatus() {
                try {
                    logMessage('DEBUG', 'Polling status...');
                    const response = await fetch('/test_status');
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const status = await response.json();
                    window.lastStatus = status; // Store for debug panel
                    logMessage('DEBUG', `Status: ${JSON.stringify(status)}`);
                    
                    if (status.running) {
                        showStatus('running', `<div class="spinner"></div>${status.progress}`);
                        setTimeout(pollStatus, 1000);  // Poll every second
                    } else if (status.error) {
                        logMessage('ERROR', `Status error: ${status.error}`);
                        showStatus('error', `❌ Error: ${status.error}`);
                        document.getElementById('startTest').disabled = false;
                        fetchServerLogs();
                    } else {
                        logMessage('INFO', 'Measurement completed successfully');
                        showStatus('success', '✅ Measurement completed successfully!');
                        showResults();
                        document.getElementById('startTest').disabled = false;
                    }
                } catch (error) {
                    logMessage('ERROR', `Status polling error: ${error.message}`);
                    showStatus('error', `❌ Status Error: ${error.message}`);
                    document.getElementById('startTest').disabled = false;
                }
            }
            
            async function fetchServerLogs() {
                try {
                    logMessage('INFO', 'Fetching server logs...');
                    const response = await fetch('/logs');
                    if (response.ok) {
                        const data = await response.json();
                        console.log('=== SERVER LOGS ===');
                        data.logs.forEach(line => console.log(line.trim()));
                        console.log('=== END SERVER LOGS ===');
                    }
                } catch (error) {
                    logMessage('ERROR', `Failed to fetch server logs: ${error.message}`);
                }
            }
            
            async function showResults() {
                try {
                    const response = await fetch('/test_results');
                    const results = await response.json();
                    
                    let html = '<h4>Generated Files:</h4><ul>';
                    results.files.forEach(file => {
                        html += `<li>📄 ${file}</li>`;
                    });
                    html += '</ul>';
                    
                    if (results.measurements.length > 0) {
                        html += '<h4>Measurements:</h4>';
                        results.measurements.forEach(m => {
                            html += `<p><strong>${m.name}:</strong> ${m.current} (Mean: ${m.mean})</p>`;
                        });
                    }
                    
                    document.getElementById('resultsContent').innerHTML = html;
                    document.getElementById('resultsPanel').style.display = 'block';
                } catch (error) {
                    console.error('Error showing results:', error);
                }
            }
            
            function showStatus(type, message) {
                const panel = document.getElementById('statusPanel');
                const content = document.getElementById('statusContent');
                
                panel.className = `status-panel status-${type}`;
                content.innerHTML = message;
                panel.style.display = 'block';
            }
            
            document.getElementById('clearForm').addEventListener('click', function() {
                document.getElementById('measurementForm').reset();
                document.getElementById('statusPanel').style.display = 'none';
                document.getElementById('resultsPanel').style.display = 'none';
                document.getElementById('debugPanel').style.display = 'none';
                document.getElementById('startTest').disabled = false;
                logMessage('INFO', 'Form cleared');
            });
            
            // Show debug panel on error or when requested
            function showDebugOnError() {
                document.getElementById('debugPanel').style.display = 'block';
                toggleDebugPanel(); // Show the content
            }
            
            // Load defaults and update form
            async function loadDefaults() {
                try {
                    const response = await fetch('/defaults');
                    if (response.ok) {
                        const defaults = await response.json();
                        applyDefaults(defaults);
                        logMessage('INFO', 'Defaults loaded successfully');
                    } else {
                        logMessage('WARNING', 'Could not load defaults from server');
                    }
                } catch (error) {
                    logMessage('WARNING', `Error loading defaults: ${error.message}`);
                }
            }
            
            function applyDefaults(defaults) {
                // Apply connection settings
                if (defaults.visa_address) {
                    document.getElementById('visa_address').value = defaults.visa_address;
                }
                
                // Apply output configuration
                if (defaults.destination) {
                    document.getElementById('destination').value = defaults.destination;
                }
                if (defaults.board_number) {
                    document.getElementById('board_number').value = defaults.board_number;
                }
                if (defaults.label) {
                    document.getElementById('label').value = defaults.label;
                }
                
                // Apply channel selections and labels
                if (defaults.channels) {
                    Object.keys(defaults.channels).forEach(channel => {
                        const checkbox = document.getElementById(channel.toLowerCase());
                        const labelInput = document.getElementById(channel.toLowerCase() + '_label');
                        
                        if (checkbox) {
                            // Handle both old boolean format and new object format
                            if (typeof defaults.channels[channel] === 'boolean') {
                                checkbox.checked = defaults.channels[channel];
                            } else if (typeof defaults.channels[channel] === 'object') {
                                checkbox.checked = defaults.channels[channel].enabled || false;
                                if (labelInput && defaults.channels[channel].label) {
                                    labelInput.value = defaults.channels[channel].label;
                                }
                            }
                        }
                    });
                }
                
                // Apply capture type selections
                if (defaults.capture_types) {
                    Object.keys(defaults.capture_types).forEach(captureType => {
                        const checkbox = document.getElementById(captureType);
                        if (checkbox) {
                            checkbox.checked = defaults.capture_types[captureType];
                        }
                    });
                }
                
                // Update path preview
                updatePathPreview();
            }
            
            function updatePathPreview() {
                const destination = document.getElementById('destination').value || './captures';
                const boardNumber = document.getElementById('board_number').value || '00001';
                const label = document.getElementById('label').value || 'Test';
                
                // Format board number to 5 digits, preserving leading zeros
                let boardNumFormatted;
                if (boardNumber === '00000') {
                    boardNumFormatted = '00000';  // Special case for 00000
                } else {
                    const num = parseInt(boardNumber) || 1;
                    boardNumFormatted = String(num).padStart(5, '0');
                }
                
                // Generate preview path
                const boardDir = `Board_${boardNumFormatted}`;
                const sessionDir = `B${boardNumFormatted}-YYYYMMDD.HHMMSS-${label}`;
                const fullPath = `${destination}/${boardDir}/${sessionDir}/`;
                
                document.getElementById('output_path_preview').textContent = fullPath;
            }
            
            // Add event listeners for path preview updates
            document.getElementById('destination').addEventListener('input', updatePathPreview);
            document.getElementById('board_number').addEventListener('input', updatePathPreview);
            document.getElementById('label').addEventListener('input', updatePathPreview);
            
            // Initialize logging
            logMessage('INFO', 'GUI initialized');
            logMessage('INFO', `User Agent: ${navigator.userAgent}`);
            logMessage('INFO', `Page URL: ${window.location.href}`);
            
            // Load defaults on startup
            loadDefaults();
            
            // Test server connectivity on startup
            setTimeout(async () => {
                try {
                    logMessage('INFO', 'Testing server connectivity...');
                    const response = await fetch('/test_status');
                    if (response.ok) {
                        const status = await response.json();
                        logMessage('INFO', `Server connection OK. Initial status: ${JSON.stringify(status)}`);
                    } else {
                        logMessage('WARNING', `Server responded with status ${response.status}`);
                    }
                } catch (error) {
                    logMessage('ERROR', `Server connectivity test failed: ${error.message}`);
                    showStatus('error', '⚠️ Warning: Cannot connect to server. Check if the server is running.');
                    showDebugOnError();
                }
            }, 1000);
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/defaults")
async def get_defaults():
    """Get default configuration values."""
    try:
        defaults = load_defaults()
        return defaults
    except Exception as e:
        logger.error(f"Error getting defaults: {e}")
        return {"error": f"Could not load defaults: {str(e)}"}

@app.post("/start_measurement")
async def start_measurement(request: Request):
    """Start the measurement capture process."""
    global current_test_status, test_results
    
    logger.info("=== START MEASUREMENT REQUEST ===")
    
    try:
        # Log client IP and headers
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Client IP: {client_ip}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Parse request data
        data = await request.json()
        logger.info(f"Request data: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        if not data.get("visa_address"):
            error_msg = "VISA address is required"
            logger.error(f"Validation error: {error_msg}")
            return {"success": False, "error": error_msg}
        
        if not data.get("destination"):
            error_msg = "Destination directory is required"
            logger.error(f"Validation error: {error_msg}")
            return {"success": False, "error": error_msg}
            
        if not data.get("board_number"):
            error_msg = "Board number is required"
            logger.error(f"Validation error: {error_msg}")
            return {"success": False, "error": error_msg}
            
        if not data.get("label"):
            error_msg = "Measurement label is required"
            logger.error(f"Validation error: {error_msg}")
            return {"success": False, "error": error_msg}
        
        # Generate the parameterized output directory
        output_dir = generate_output_path(
            data.get("destination"),
            data.get("board_number"), 
            data.get("label")
        )
        logger.info(f"Generated output path: {output_dir}")
        
        # Add the generated output_dir back to data for compatibility
        data["output_dir"] = output_dir
        
        # Reset status
        current_test_status = {"running": True, "progress": "Initializing...", "error": None}
        test_results = {"files": [], "measurements": []}
        logger.info("Status reset, starting background task...")
        
        # Start the measurement in background
        task = asyncio.create_task(run_measurement_capture(data))
        logger.info(f"Background task created: {task}")
        
        response = {"success": True, "message": "Measurement started"}
        logger.info(f"Returning response: {response}")
        return response
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in request: {str(e)}"
        logger.error(error_msg)
        current_test_status = {"running": False, "progress": "", "error": error_msg}
        return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error in start_measurement: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        current_test_status = {"running": False, "progress": "", "error": error_msg}
        return {"success": False, "error": error_msg}

async def save_channel_metadata(config):
    """Save channel metadata for report generation."""
    try:
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "channels": {}
        }
        
        # Extract channel labels from config
        if config.get("channel_labels"):
            for channel, channel_config in config["channel_labels"].items():
                metadata["channels"][channel] = {
                    "label": channel_config.get("label", f"{channel} Default"),
                    "enabled": channel_config.get("enabled", True)
                }
        
        # Default labels for channels that don't have custom labels
        default_labels = {
            "CH1": "Channel 1",
            "CH2": "Channel 2", 
            "CH3": "Channel 3",
            "CH4": "Channel 4",
            "M1": "Math 1"
        }
        
        # Ensure all selected channels have metadata
        if config.get("channels"):
            for channel in config["channels"]:
                if channel not in metadata["channels"]:
                    metadata["channels"][channel] = {
                        "label": default_labels.get(channel, f"{channel} Default"),
                        "enabled": True
                    }
        
        # Save metadata to output directory
        output_dir = Path(config["output_dir"])
        metadata_file = output_dir / "channel_metadata.json"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Channel metadata saved to: {metadata_file}")
        
    except Exception as e:
        logger.error(f"Error saving channel metadata: {e}")

async def save_measurement_notes(config):
    """Save measurement notes to the output directory."""
    try:
        output_dir = Path(config["output_dir"])
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        notes = config.get("notes", "")
        if notes.strip():
            # Save notes as both markdown and text
            notes_md_file = output_dir / "measurement_notes.md"
            notes_txt_file = output_dir / "measurement_notes.txt"
            
            # Save as markdown
            with open(notes_md_file, 'w', encoding='utf-8') as f:
                f.write(notes)
            
            # Save as plain text (for compatibility)
            with open(notes_txt_file, 'w', encoding='utf-8') as f:
                f.write(notes)
                
            logger.info(f"Measurement notes saved to: {notes_md_file}")
        
        # Copy uploaded images to the measurement directory
        await copy_images_to_output(config)
        
    except Exception as e:
        logger.error(f"Error saving measurement notes: {e}")

async def copy_images_to_output(config):
    """Copy uploaded images from temp directory to the output directory."""
    try:
        output_dir = Path(config["output_dir"])
        images_dir = output_dir / "images"
        
        # Get all uploaded images
        if temp_dir.exists():
            image_files = []
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    if mime_type and mime_type.startswith('image/'):
                        image_files.append(file_path)
            
            if image_files:
                images_dir.mkdir(exist_ok=True)
                
                for image_file in image_files:
                    dest_path = images_dir / image_file.name
                    shutil.copy2(image_file, dest_path)
                    logger.info(f"Copied image: {image_file.name} to {dest_path}")
                
                logger.info(f"Copied {len(image_files)} images to {images_dir}")
        
    except Exception as e:
        logger.error(f"Error copying images to output: {e}")

async def run_measurement_capture(config):
    """Run the measurement capture process."""
    global current_test_status, test_results
    
    logger.info("=== MEASUREMENT CAPTURE STARTED ===")
    logger.info(f"Config: {json.dumps(config, indent=2)}")
    
    try:
        # Update progress
        current_test_status["progress"] = "Connecting to oscilloscope..."
        logger.info("Progress: Connecting to oscilloscope...")
        
        # Get Python executable path
        python_exe = "C:/Users/10588/OneDrive - Redlen Technologies/Development/Lab_Data_Logging/.venv/Scripts/python.exe"
        logger.info(f"Using Python executable: {python_exe}")
        
        # Build command
        cmd = [
            python_exe, "test_measurement_results.py",
            config["visa_address"],
            "--output-dir", config["output_dir"]
        ]
        
        # Add channel options if specified
        if config.get("channels"):
            for channel in config["channels"]:
                cmd.extend(["--channel", channel])
                
        # Add capture type options
        capture_types = config.get("capture_types", [])
        if "screenshot" not in capture_types:
            cmd.append("--no-screenshot")
        if "waveforms" not in capture_types:
            cmd.append("--no-waveforms")
        
        # Save channel metadata for report generation
        await save_channel_metadata(config)
        
        # Save notes if provided
        if config.get("notes"):
            await save_measurement_notes(config)
        
        logger.info(f"Command to execute: {' '.join(cmd)}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        current_test_status["progress"] = "Running measurement capture..."
        logger.info("Progress: Running measurement capture...")
        
        # Run the measurement script
        logger.info("Creating subprocess...")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        logger.info(f"Subprocess created with PID: {process.pid}")
        
        # Wait for process completion
        logger.info("Waiting for process to complete...")
        stdout, stderr = await process.communicate()
        
        logger.info(f"Process completed with return code: {process.returncode}")
        
        # Log output
        stdout_text = stdout.decode('utf-8', errors='replace')
        stderr_text = stderr.decode('utf-8', errors='replace')
        
        logger.info(f"STDOUT ({len(stdout_text)} chars):")
        logger.info(stdout_text)
        
        if stderr_text:
            logger.error(f"STDERR ({len(stderr_text)} chars):")
            logger.error(stderr_text)
        
        if process.returncode == 0:
            current_test_status["progress"] = "Processing results..."
            logger.info("Progress: Processing results...")
            
            # Parse output to extract file information
            files = []
            
            # Extract file paths from output
            for line in stdout_text.split('\n'):
                if 'saved:' in line.lower() or 'generated:' in line.lower():
                    # Extract file path
                    parts = line.split(':')
                    if len(parts) > 1:
                        file_path = parts[-1].strip()
                        files.append(file_path)
                        logger.info(f"Found file: {file_path}")
            
            test_results["files"] = files
            logger.info(f"Total files found: {len(files)}")
            
            # Generate HTML report if requested
            if "html_report" in capture_types:
                current_test_status["progress"] = "Generating HTML report..."
                logger.info("Progress: Generating HTML report...")
                
                report_cmd = [
                    python_exe, "generate_static_report.py",
                    config["output_dir"],
                    "--output", f"{config['output_dir']}/measurement_report.html"
                ]
                
                logger.info(f"Report command: {' '.join(report_cmd)}")
                
                report_process = await asyncio.create_subprocess_exec(
                    *report_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.getcwd()
                )
                
                report_stdout, report_stderr = await report_process.communicate()
                
                logger.info(f"Report process return code: {report_process.returncode}")
                logger.info(f"Report STDOUT: {report_stdout.decode('utf-8', errors='replace')}")
                
                if report_stderr:
                    logger.error(f"Report STDERR: {report_stderr.decode('utf-8', errors='replace')}")
                
                if report_process.returncode == 0:
                    report_file = f"{config['output_dir']}/measurement_report.html"
                    test_results["files"].append(report_file)
                    logger.info(f"Report generated: {report_file}")
            
            current_test_status = {"running": False, "progress": "Completed", "error": None}
            logger.info("=== MEASUREMENT CAPTURE COMPLETED SUCCESSFULLY ===")
            
        else:
            error_text = f"Process failed with return code {process.returncode}. STDERR: {stderr_text}"
            current_test_status = {"running": False, "progress": "", "error": error_text}
            logger.error(f"Measurement failed: {error_text}")
            
    except Exception as e:
        error_msg = f"Exception in run_measurement_capture: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        current_test_status = {"running": False, "progress": "", "error": error_msg}

@app.get("/test_status")
async def get_test_status():
    """Get current test status."""
    logger.debug(f"Status requested: {current_test_status}")
    return current_test_status

@app.get("/test_results")
async def get_test_results():
    """Get test results."""
    logger.info(f"Results requested: {test_results}")
    return test_results

@app.get("/logs")
async def get_logs():
    """Get recent log entries."""
    try:
        log_file = Path("measurement_gui.log")
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
            # Return last 50 lines
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            return {"logs": recent_lines}
        else:
            return {"logs": ["Log file not found"]}
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return {"logs": [f"Error reading logs: {e}"]}

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to the temp directory."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={"error": "Only image files are allowed"}
            )
        
        # Generate unique filename to prevent conflicts
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Save file to temp directory
        file_path = temp_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Image uploaded: {unique_filename} (original: {file.filename})")
        
        return JSONResponse(content={
            "success": True,
            "filename": unique_filename,
            "original_name": file.filename
        })
        
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to upload image: {str(e)}"}
        )

@app.get("/list_images")
async def list_images():
    """List all uploaded images in the temp directory."""
    try:
        image_files = []
        if temp_dir.exists():
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    # Check if it's an image file
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    if mime_type and mime_type.startswith('image/'):
                        image_files.append(file_path.name)
        
        # Sort by modification time (newest first)
        image_files.sort(key=lambda x: (temp_dir / x).stat().st_mtime, reverse=True)
        
        return image_files
        
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to list images: {str(e)}"}
        )

@app.delete("/delete_image/{filename}")
async def delete_image(filename: str):
    """Delete an uploaded image."""
    try:
        file_path = temp_dir / filename
        
        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "Image not found"}
            )
        
        # Verify it's within the temp directory (security check)
        if not str(file_path.resolve()).startswith(str(temp_dir.resolve())):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid file path"}
            )
        
        file_path.unlink()
        logger.info(f"Image deleted: {filename}")
        
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to delete image: {str(e)}"}
        )

if __name__ == "__main__":
    print("🚀 Starting Oscilloscope Measurement GUI...")
    print("🌐 Open your browser to: http://localhost:8081")
    print("💡 Use Ctrl+C to stop the server")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8081,
        log_level="info"
    )