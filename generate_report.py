#!/usr/bin/env python3
"""
HTML Report Generator for Keysight MSOX4154A Measurement Results

This script generates an interactive HTML report from oscilloscope measurement data.
It includes:
- Tabulated measurement results
- Screenshot display
- Interactive plots for CH1 and M1 waveforms (served via FastAPI)

Usage:
    python generate_report.py <input_directory> [--output output.html] [--port 8000]

Requirements:
    - FastAPI, Uvicorn for web server
    - Plotly for interactive plots
    - Pandas for data handling

Author: Redlen Technologies Lab Automation Team
Date: 2025-10
"""

import sys
import argparse
import asyncio
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import base64

# Web server imports
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Data processing imports
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

class MeasurementReportGenerator:
    """Generates HTML reports from oscilloscope measurement data."""
    
    def __init__(self, input_dir: str, port: int = 8000):
        self.input_dir = Path(input_dir)
        self.port = port
        self.app = FastAPI()
        self.setup_routes()
        
        # Data storage
        self.measurement_data = {}
        self.ch1_data = None
        self.m1_data = None
        self.screenshot_b64 = None
        
    def setup_routes(self):
        """Setup FastAPI routes for serving plot data."""
        
        @self.app.get("/")
        async def root():
            return {"message": "Measurement Report Server"}
        
        @self.app.get("/plot/ch1")
        async def get_ch1_plot():
            """Return CH1 waveform plot as JSON."""
            if self.ch1_data is None:
                raise HTTPException(status_code=404, detail="CH1 data not found")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.ch1_data['Time_s'],
                y=self.ch1_data['Voltage_V'],
                mode='lines',
                name='CH1 Voltage',
                line=dict(color='#1f77b4', width=1)
            ))
            
            fig.update_layout(
                title="CH1 Waveform",
                xaxis_title="Time (s)",
                yaxis_title="Voltage (V)",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            return JSONResponse(content=json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)))
        
        @self.app.get("/plot/m1")
        async def get_m1_plot():
            """Return M1 waveform plot as JSON."""
            if self.m1_data is None:
                raise HTTPException(status_code=404, detail="M1 data not found")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.m1_data['Time_s'],
                y=self.m1_data['Value'],
                mode='lines+markers',
                name='M1 Math Function',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                title="M1 Math Waveform",
                xaxis_title="Time (s)",
                yaxis_title="Value",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            return JSONResponse(content=json.loads(json.dumps(fig, cls=PlotlyJSONEncoder)))
    
    def load_data(self):
        """Load all measurement data from input directory."""
        print(f"Loading data from: {self.input_dir}")
        
        # Find files
        txt_files = list(self.input_dir.glob("measurement_results_*.txt"))
        ch1_files = list(self.input_dir.glob("ch1_waveform_*.csv"))
        m1_files = list(self.input_dir.glob("m1_waveform_*.csv"))
        screenshot_files = list(self.input_dir.glob("measurement_results_screenshot_*.png"))
        
        if not txt_files:
            raise FileNotFoundError("No measurement results txt file found")
        
        # Load measurement results
        self.load_measurement_results(txt_files[0])
        
        # Load waveform data
        if ch1_files:
            print(f"Loading CH1 data from: {ch1_files[0]}")
            self.ch1_data = pd.read_csv(ch1_files[0])
            print(f"  CH1: {len(self.ch1_data)} samples")
        
        if m1_files:
            print(f"Loading M1 data from: {m1_files[0]}")
            self.m1_data = pd.read_csv(m1_files[0])
            print(f"  M1: {len(self.m1_data)} samples")
        
        # Load screenshot
        if screenshot_files:
            print(f"Loading screenshot: {screenshot_files[0]}")
            self.load_screenshot(screenshot_files[0])
    
    def load_measurement_results(self, txt_file: Path):
        """Parse measurement results from txt file."""
        with open(txt_file, 'r') as f:
            content = f.read()
        
        # Extract basic info
        lines = content.split('\n')
        self.measurement_data = {
            'timestamp': '',
            'statistics_mode': '',
            'raw_response': '',
            'measurements': []
        }
        
        current_measurement = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Timestamp:'):
                self.measurement_data['timestamp'] = line.split(':', 1)[1].strip()
            elif line.startswith('Statistics Mode:'):
                self.measurement_data['statistics_mode'] = line.split(':', 1)[1].strip()
            elif line.startswith('Raw Response:'):
                self.measurement_data['raw_response'] = line.split(':', 1)[1].strip()
            elif line.startswith('Measurement ') and ':' in line:
                # New measurement
                if current_measurement:
                    self.measurement_data['measurements'].append(current_measurement)
                
                name = line.split(':', 1)[1].strip()
                current_measurement = {'name': name, 'values': {}}
                
            elif current_measurement and ':' in line and any(x in line for x in ['Current:', 'Minimum:', 'Maximum:', 'Mean:', 'Std Dev:', 'Count:']):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                current_measurement['values'][key] = value
        
        # Add the last measurement
        if current_measurement:
            self.measurement_data['measurements'].append(current_measurement)
    
    def load_screenshot(self, screenshot_file: Path):
        """Load and encode screenshot as base64."""
        with open(screenshot_file, 'rb') as f:
            screenshot_data = f.read()
        self.screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
    
    def generate_html_report(self, output_file: str = "measurement_report.html"):
        """Generate the HTML report."""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oscilloscope Measurement Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1f77b4;
            margin: 0;
            font-size: 2.5em;
        }}
        .header h2 {{
            color: #666;
            margin: 5px 0 0 0;
            font-weight: normal;
        }}
        .info-section {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .info-section h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .measurements-table {{
            width: 100%%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        .measurements-table th,
        .measurements-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .measurements-table th {{
            background-color: #1f77b4;
            color: white;
            font-weight: bold;
        }}
        .measurements-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .screenshot-section {{
            text-align: center;
            margin: 30px 0;
        }}
        .screenshot-section img {{
            max-width: 100%%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 5px;
        }}
        .plots-section {{
            margin-top: 30px;
        }}
        .plot-container {{
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }}
        .plot-title {{
            background-color: #1f77b4;
            color: white;
            padding: 10px 15px;
            margin: 0;
            font-size: 1.2em;
        }}
        .plot-content {{
            padding: 10px;
        }}
        .loading {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        .error {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Keysight MSOX4154A</h1>
            <h2>Measurement Report</h2>
        </div>
        
        <div class="info-section">
            <h3>Test Information</h3>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>Statistics Mode:</strong> {statistics_mode}</p>
            <p><strong>Input Directory:</strong> {input_dir}</p>
            <p><strong>Raw Response:</strong> <code>{raw_response}</code></p>
        </div>
        
        <h3>Measurement Results</h3>
        <table class="measurements-table">
            <thead>
                <tr>
                    <th>Measurement</th>
                    <th>Current</th>
                    <th>Minimum</th>
                    <th>Maximum</th>
                    <th>Mean</th>
                    <th>Std Dev</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                {measurements_rows}
            </tbody>
        </table>
        
        {screenshot_section}
        
        <div class="plots-section">
            <h3>Interactive Waveform Plots</h3>
            
            <div class="plot-container">
                <h4 class="plot-title">CH1 Waveform</h4>
                <div class="plot-content">
                    <div id="ch1-plot" class="loading">Loading CH1 plot...</div>
                </div>
            </div>
            
            <div class="plot-container">
                <h4 class="plot-title">M1 Math Waveform</h4>
                <div class="plot-content">
                    <div id="m1-plot" class="loading">Loading M1 plot...</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Lab Data Logging Framework - Redlen Technologies</p>
            <p>Report created on {generation_time}</p>
        </div>
    </div>
    
    <script>
        // Load plots from FastAPI server
        const SERVER_PORT = {port};
        
        async function loadPlot(endpoint, elementId) {{
            try {{
                const response = await fetch(`http://localhost:${{SERVER_PORT}}/plot/${{endpoint}}`);
                if (!response.ok) {{
                    throw new Error(`HTTP error! status: ${{response.status}}`);
                }}
                const plotData = await response.json();
                Plotly.newPlot(elementId, plotData.data, plotData.layout, {{responsive: true}});
            }} catch (error) {{
                console.error(`Error loading ${{endpoint}} plot:`, error);
                document.getElementById(elementId).innerHTML = 
                    `<div class="error">Error loading ${{endpoint.toUpperCase()}} plot: ${{error.message}}</div>`;
            }}
        }}
        
        // Load plots when page loads
        window.addEventListener('load', function() {{
            loadPlot('ch1', 'ch1-plot');
            loadPlot('m1', 'm1-plot');
        }});
    </script>
</body>
</html>
        """
        
        # Generate measurements table rows
        measurements_rows = ""
        for measurement in self.measurement_data['measurements']:
            name = measurement['name']
            values = measurement['values']
            measurements_rows += f"""
                <tr>
                    <td><strong>{name}</strong></td>
                    <td>{values.get('Current', 'N/A')}</td>
                    <td>{values.get('Minimum', 'N/A')}</td>
                    <td>{values.get('Maximum', 'N/A')}</td>
                    <td>{values.get('Mean', 'N/A')}</td>
                    <td>{values.get('Std Dev', 'N/A')}</td>
                    <td>{values.get('Count', 'N/A')}</td>
                </tr>
            """
        
        # Generate screenshot section
        screenshot_section = ""
        if self.screenshot_b64:
            screenshot_section = f"""
        <div class="screenshot-section">
            <h3>Oscilloscope Screenshot</h3>
            <img src="data:image/png;base64,{self.screenshot_b64}" alt="Oscilloscope Screenshot">
        </div>
            """
        
        # Fill template
        html_content = html_template.format(
            timestamp=self.measurement_data.get('timestamp', 'Unknown'),
            statistics_mode=self.measurement_data.get('statistics_mode', 'Unknown'),
            input_dir=str(self.input_dir),
            raw_response=self.measurement_data.get('raw_response', ''),
            measurements_rows=measurements_rows,
            screenshot_section=screenshot_section,
            port=self.port,
            generation_time=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Write HTML file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_path.absolute()}")
        return output_path
    
    def start_server(self):
        """Start the FastAPI server in a separate thread."""
        def run_server():
            uvicorn.run(self.app, host="127.0.0.1", port=self.port, log_level="warning")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print(f"FastAPI server starting on http://localhost:{self.port}")
        time.sleep(2)  # Give server time to start
        return server_thread

def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description="Generate interactive HTML report from oscilloscope measurement data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_report.py ./captures/Board_00003/VDD_1V45_L/
  python generate_report.py ./captures/Board_00003/VDD_1V45_L/ --output custom_report.html
  python generate_report.py ./captures/Board_00003/VDD_1V45_L/ --port 8080
        """
    )
    
    parser.add_argument(
        "input_dir",
        help="Input directory containing measurement files"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="measurement_report.html",
        help="Output HTML file name (default: measurement_report.html)"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port for FastAPI server (default: 8000)"
    )
    
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser"
    )
    
    args = parser.parse_args()
    
    try:
        print("Keysight MSOX4154A - HTML Report Generator")
        print("=" * 50)
        
        # Create report generator
        generator = MeasurementReportGenerator(args.input_dir, args.port)
        
        # Load data
        generator.load_data()
        
        # Start server
        server_thread = generator.start_server()
        
        # Generate HTML report
        report_path = generator.generate_html_report(args.output)
        
        print("\nReport generation completed successfully!")
        print(f"HTML Report: {report_path}")
        print(f"FastAPI Server: http://localhost:{args.port}")
        
        if not args.no_browser:
            print("\nOpening report in browser...")
            webbrowser.open(f"file://{report_path.absolute()}")
        
        print("\nPress Ctrl+C to stop the server and exit.")
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())