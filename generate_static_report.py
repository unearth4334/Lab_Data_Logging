#!/usr/bin/env python3
"""
Static HTML Report Generator for Keysight MSOX4154A Measurement Results

This script generates a static HTML report from oscilloscope measurement data.
It includes:
- Tabulated measurement results
- Screenshot display
- Static interactive plots for CH1 and M1 waveforms (embedded in HTML)

Usage:
    python generate_static_report.py <input_directory> [--output output.html]

Requirements:
    - Pandas for data handling
    - Plotly for interactive plots

Author: Redlen Technologies Lab Automation Team
Date: 2025-10
"""

import sys
import argparse
import time
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import base64

# Data processing imports
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as pyo

class StaticMeasurementReportGenerator:
    """Generates static HTML reports from oscilloscope measurement data."""
    
    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        
        # Data storage
        self.measurement_data = {}
        self.ch1_data = None
        self.m1_data = None
        self.screenshot_b64 = None
        
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
    
    def create_ch1_plot(self):
        """Create CH1 waveform plot."""
        if self.ch1_data is None:
            return "<p>No CH1 data available</p>"
        
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
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def create_m1_plot(self):
        """Create M1 waveform plot."""
        if self.m1_data is None:
            return "<p>No M1 data available</p>"
        
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
        
        return pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
    def generate_html_report(self, output_file: str = "measurement_report.html"):
        """Generate the static HTML report."""
        
        # Create plots
        ch1_plot_html = self.create_ch1_plot()
        m1_plot_html = self.create_m1_plot()
        
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
            width: 100%;
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
            max-width: 100%;
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
                    {ch1_plot}
                </div>
            </div>
            
            <div class="plot-container">
                <h4 class="plot-title">M1 Math Waveform</h4>
                <div class="plot-content">
                    {m1_plot}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Lab Data Logging Framework - Redlen Technologies</p>
            <p>Report created on {generation_time}</p>
        </div>
    </div>
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
            ch1_plot=ch1_plot_html,
            m1_plot=m1_plot_html,
            generation_time=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Write HTML file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Static HTML report generated: {output_path.absolute()}")
        return output_path

def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description="Generate static HTML report from oscilloscope measurement data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_static_report.py ./captures/Board_00003/VDD_1V45_L/
  python generate_static_report.py ./captures/Board_00003/VDD_1V45_L/ --output custom_report.html
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
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser"
    )
    
    args = parser.parse_args()
    
    try:
        print("Keysight MSOX4154A - Static HTML Report Generator")
        print("=" * 55)
        
        # Create report generator
        generator = StaticMeasurementReportGenerator(args.input_dir)
        
        # Load data
        generator.load_data()
        
        # Generate HTML report
        report_path = generator.generate_html_report(args.output)
        
        print("\nReport generation completed successfully!")
        print(f"HTML Report: {report_path}")
        
        if not args.no_browser:
            print("\nOpening report in browser...")
            webbrowser.open(f"file://{report_path.absolute()}")
        
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())