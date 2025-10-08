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

Au        .plots-section {
            margin-top: 30px;
        }
        .plot-section {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
            background-color: white;
        }
        .plot-section h3 {
            background-color: #1f77b4;
            color: white;
            padding: 10px 15px;
            margin: 0;
            font-size: 1.2em;
        }
        .plot-wrapper {
            padding: 10px;
        }
        .interactive-plot {
            width: 100%;
            height: auto;
        }
        .static-plot {
            text-align: center;
        }
        /* Legacy classes for backward compatibility */
        .plot-container {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        .plot-title {
            background-color: #1f77b4;
            color: white;
            padding: 10px 15px;
            margin: 0;
            font-size: 1.2em;
        }
        .plot-content {
            padding: 10px;
        }logies Lab Automation Team
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
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io

# Markdown processing
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

class StaticMeasurementReportGenerator:
    """Generates static HTML reports from oscilloscope measurement data."""
    
    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        
        # Data storage
        self.measurement_data = {}
        self.channel_data = {}  # Will store data for all channels (CH1-CH4, M1)
        self.channel_metadata = {}  # Will store channel labels and settings
        self.screenshot_b64 = None
        self.measurement_notes_html = ""
        self.csv_data_b64 = {}  # Will store base64-encoded CSV data for embedding
        
    def load_channel_metadata(self):
        """Load channel metadata (labels, colors) if available."""
        metadata_file = self.input_dir / "channel_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.channel_metadata = metadata.get("channels", {})
                    print(f"Loaded channel metadata: {self.channel_metadata}")
            except Exception as e:
                print(f"Warning: Could not load channel metadata: {e}")
                self.channel_metadata = {}
        else:
            print("No channel metadata file found, using defaults")
            self.channel_metadata = {}

    def load_data(self):
        """Load all measurement data from input directory."""
        print(f"Loading data from: {self.input_dir}")
        
        # Load channel metadata first
        self.load_channel_metadata()
        
        # Find files - support both old and new filename patterns
        txt_files = list(self.input_dir.glob("results_*.txt"))
        if not txt_files:
            txt_files = list(self.input_dir.glob("measurement_results_*.txt"))
        
        ch1_files = list(self.input_dir.glob("ch1_waveform_*.csv"))
        m1_files = list(self.input_dir.glob("m1_waveform_*.csv"))
        
        screenshot_files = list(self.input_dir.glob("screenshot_*.png"))
        if not screenshot_files:
            screenshot_files = list(self.input_dir.glob("measurement_results_screenshot_*.png"))
        
        if not txt_files:
            raise FileNotFoundError("No measurement results txt file found (tried both 'results_*.txt' and 'measurement_results_*.txt' patterns)")
        
        # Load measurement results
        self.load_measurement_results(txt_files[0])
        
        # Load waveform data dynamically for all channels
        channel_patterns = {
            'CH1': 'ch1_*.csv',
            'CH2': 'ch2_*.csv', 
            'CH3': 'ch3_*.csv',
            'CH4': 'ch4_*.csv',
            'M1': 'm1_*.csv'
        }
        
        for channel, pattern in channel_patterns.items():
            channel_files = list(self.input_dir.glob(pattern))
            if channel_files:
                print(f"Loading {channel} data from: {channel_files[0]}")
                self.channel_data[channel] = pd.read_csv(channel_files[0])
                print(f"  {channel}: {len(self.channel_data[channel])} samples")
                
                # Also store the raw CSV data as base64 for embedding
                with open(channel_files[0], 'rb') as f:
                    csv_content = f.read()
                    self.csv_data_b64[channel] = base64.b64encode(csv_content).decode('utf-8')
        
        # Load screenshot
        if screenshot_files:
            print(f"Loading screenshot: {screenshot_files[0]}")
            self.load_screenshot(screenshot_files[0])
        
        # Load measurement notes
        self.measurement_notes_html = self.load_measurement_notes()
    
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
            'measurements': [],
            'config': {}
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
            elif line.startswith('Acquisition Mode:'):
                self.measurement_data['config']['acquisition_mode'] = line.split(':', 1)[1].strip()
            elif line.startswith('Time Scale:'):
                self.measurement_data['config']['time_scale'] = line.split(':', 1)[1].strip()
            # Parse channel configuration dynamically
            elif 'Scale:' in line and any(f'CH{i}' in line for i in range(1, 5)):
                for ch_num in range(1, 5):
                    if line.startswith(f'CH{ch_num} Scale:'):
                        self.measurement_data['config'][f'ch{ch_num}_scale'] = line.split(':', 1)[1].strip()
                        break
            elif 'Bandwidth Limit:' in line and any(f'CH{i}' in line for i in range(1, 5)):
                for ch_num in range(1, 5):
                    if line.startswith(f'CH{ch_num} Bandwidth Limit:'):
                        self.measurement_data['config'][f'ch{ch_num}_bandwidth_limit'] = line.split(':', 1)[1].strip()
                        break
            elif 'Coupling:' in line and any(f'CH{i}' in line for i in range(1, 5)):
                for ch_num in range(1, 5):
                    if line.startswith(f'CH{ch_num} Coupling:'):
                        self.measurement_data['config'][f'ch{ch_num}_coupling'] = line.split(':', 1)[1].strip()
                        break
            elif 'Offset:' in line and any(f'CH{i}' in line for i in range(1, 5)):
                for ch_num in range(1, 5):
                    if line.startswith(f'CH{ch_num} Offset:'):
                        self.measurement_data['config'][f'ch{ch_num}_offset'] = line.split(':', 1)[1].strip()
                        break
            elif 'Display:' in line and any(f'CH{i}' in line for i in range(1, 5)):
                for ch_num in range(1, 5):
                    if line.startswith(f'CH{ch_num} Display:'):
                        self.measurement_data['config'][f'ch{ch_num}_display'] = line.split(':', 1)[1].strip()
                        break
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
    
    def load_measurement_notes(self):
        """Load measurement notes from markdown file and convert to HTML."""
        notes_file = self.input_dir / "measurement_notes.md"
        notes_html = ""
        
        if notes_file.exists():
            try:
                with open(notes_file, 'r', encoding='utf-8') as f:
                    notes_content = f.read().strip()
                
                if notes_content:
                    if MARKDOWN_AVAILABLE:
                        # Convert markdown to HTML
                        import markdown
                        md = markdown.Markdown(extensions=['extra', 'codehilite'])
                        notes_html = md.convert(notes_content)
                    else:
                        # Fallback: simple HTML conversion
                        notes_html = self._simple_markdown_to_html(notes_content)
                        
                    print(f"Loaded measurement notes: {len(notes_content)} characters")
                else:
                    print("Measurement notes file is empty")
            except Exception as e:
                print(f"Error loading measurement notes: {e}")
                notes_html = ""
        else:
            print("No measurement notes file found")
            
        return notes_html
    
    def _simple_markdown_to_html(self, text):
        """Simple markdown to HTML converter for fallback."""
        import re
        
        # Convert basic markdown to HTML
        # Headers
        text = re.sub(r'^### (.*$)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*$)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*$)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Bold and italic
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Images - handle both relative and absolute paths
        text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" style="max-width: 100%; height: auto;">', text)
        
        # Links
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        # Line breaks and paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip()]
        text = '\n'.join(paragraphs)
        
        return text
    
    def create_channel_plot(self, channel):
        """Create waveform plot for any channel."""
        if channel not in self.channel_data or self.channel_data[channel] is None:
            return f"<p>No {channel} data available</p>"
        
        data = self.channel_data[channel]
        print(f"Creating {channel} plot with {len(data)} points")
        
        # Determine column names and colors based on channel type
        channel_colors = {
            'CH1': 'yellow',
            'CH2': 'lime', 
            'CH3': 'cyan',
            'CH4': 'magenta',
            'M1': 'indigo'
        }
        
        if channel.startswith('CH'):
            y_col = 'Voltage_V'
            y_label = 'Voltage (V)'
            color = channel_colors.get(channel, '#1f77b4')
        else:  # M1 or other math channels
            y_col = 'Value'
            y_label = 'Value'
            color = channel_colors.get(channel, 'orange')
        
        print(f"Time range: {data['Time_s'].min():.6f} to {data['Time_s'].max():.6f} s")
        print(f"{y_label} range: {data[y_col].min():.6f} to {data[y_col].max():.6f}")
        
        return self._create_plot_with_fallback(channel, data, y_col, y_label, color)
    
    def _create_plot_with_fallback(self, channel, data, y_col, y_label, color):
        """Create plot with static fallback."""
        # Get custom channel label if available
        channel_label = self.channel_metadata.get(channel, {}).get("label", channel)
        
        try:
            print(f"  Creating interactive {channel} plot...")
            # Try interactive plot first
            fig = go.Figure()
            mode = 'lines+markers' if channel.startswith('M') else 'lines'
            marker_size = 4 if channel.startswith('M') else 2
            
            fig.add_trace(go.Scatter(
                x=data['Time_s'],
                y=data[y_col],
                mode=mode,
                name=f'{channel_label} {y_label.split("(")[0].strip()}',
                line=dict(color=color, width=2),
                marker=dict(size=marker_size) if 'markers' in mode else None
            ))
            
            fig.update_layout(
                title=f"{channel_label} Waveform ({len(data)} samples)",
                xaxis_title="Time (s)",
                yaxis_title=y_label,
                hovermode='x unified',
                template='plotly_white',
                height=400,
                showlegend=True
            )
            
            print(f"  Generating {channel} Plotly HTML...")
            interactive_plot = pyo.plot(fig, output_type='div', include_plotlyjs='inline')
            print(f"  {channel} interactive plot generated successfully")
            
            # Create static fallback
            print(f"  Creating {channel} static fallback...")
            static_plot_b64 = self._create_static_plot(channel, data, y_col, y_label, color, mode, channel_label)
            
            if static_plot_b64:
                return f'''
                <div class="plot-wrapper">
                    <div class="interactive-plot" id="{channel.lower()}-interactive">
                        {interactive_plot}
                    </div>
                    <div class="static-plot" style="display: none;" id="{channel.lower()}-static">
                        <img src="data:image/png;base64,{static_plot_b64}" alt="{channel} Waveform" style="max-width: 100%; height: auto;">
                        <p><em>Static fallback plot - interactive plot failed to load</em></p>
                    </div>
                    <script>
                        // Check if Plotly loaded correctly, if not show static plot
                        function check{channel}Plot() {{
                            var plotDiv = document.querySelector('#{channel.lower()}-interactive .plotly-graph-div');
                            if (plotDiv && window.Plotly) {{
                                console.log('{channel} interactive plot loaded successfully');
                                return; // Plot loaded successfully
                            }}
                            
                            // Try again after a longer delay
                            setTimeout(function() {{
                                var plotDiv2 = document.querySelector('#{channel.lower()}-interactive .plotly-graph-div');
                                if (!plotDiv2 || !window.Plotly) {{
                                    console.log('{channel} falling back to static plot');
                                    document.getElementById('{channel.lower()}-interactive').style.display = 'none';
                                    document.getElementById('{channel.lower()}-static').style.display = 'block';
                                }} else {{
                                    console.log('{channel} interactive plot loaded after delay');
                                }}
                            }}, 3000);
                        }}
                        
                        // Initial check after DOM is ready
                        if (document.readyState === 'loading') {{
                            document.addEventListener('DOMContentLoaded', function() {{
                                setTimeout(check{channel}Plot, 1000);
                            }});
                        }} else {{
                            setTimeout(check{channel}Plot, 1000);
                        }}
                    </script>
                </div>
                '''
            else:
                return interactive_plot
                
        except Exception as e:
            print(f"Interactive {channel} plot failed: {e}")
            # Fall back to static plot only
            static_plot_b64 = self._create_static_plot(channel, data, y_col, y_label, color, 'lines', channel_label)
            if static_plot_b64:
                return f'<img src="data:image/png;base64,{static_plot_b64}" alt="{channel} Waveform" style="max-width: 100%; height: auto;">'
            else:
                return f"<p>Failed to create {channel} plot</p>"
    
    def _create_static_plot(self, channel, data, y_col, y_label, color, mode, channel_label=None):
        """Create static plot as fallback."""
        if channel_label is None:
            channel_label = channel
            
        try:
            plt.figure(figsize=(12, 4))
            
            if 'markers' in mode:
                plt.plot(data['Time_s'], data[y_col], 
                        color=color, linewidth=2, marker='o', markersize=4, 
                        label=f'{channel_label} {y_label.split("(")[0].strip()}')
            else:
                plt.plot(data['Time_s'], data[y_col], 
                        color=color, linewidth=1, 
                        label=f'{channel_label} {y_label.split("(")[0].strip()}')
            
            plt.title(f'{channel_label} Waveform ({len(data)} samples)')
            plt.xlabel('Time (s)')
            plt.ylabel(y_label)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return plot_data
        except Exception as e:
            print(f"Failed to create static {channel} plot: {e}")
            return None
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=self.ch1_data['Time_s'],
            y=self.ch1_data['Voltage_V'],
            mode='lines',
            name='CH1 Voltage',
            line=dict(color='#1f77b4', width=1)
        ))
        
        fig.update_layout(
            title=f"CH1 Waveform ({len(self.ch1_data)} samples)",
            xaxis_title="Time (s)",
            yaxis_title="Voltage (V)",
            hovermode='x unified',
            template='plotly_white',
            height=400,
            showlegend=True
        )
        
        return pyo.plot(fig, output_type='div', include_plotlyjs='inline')
    

    def create_channel_config_html(self):
        """Create HTML for channel configurations using tile-style callouts."""
        config = self.measurement_data.get('config', {})
        channel_configs = []
        
        # Define channel colors for tile banners
        channel_colors = {
            'CH1': 'yellow',
            'CH2': 'lime', 
            'CH3': 'cyan',
            'CH4': 'magenta',
            'M1': 'indigo'
        }
        
        # Check for active channels (CH1-CH4)
        for ch_num in range(1, 5):  # CH1-CH4
            ch_name = f"ch{ch_num}"
            if (f'{ch_name}_scale' in config or 
                f'CH{ch_num}' in self.channel_data or
                config.get(f'{ch_name}_display', '').strip() == '1'):  # Check if channel is active
                
                scale = config.get(f'{ch_name}_scale', 'Unknown')
                bandwidth = config.get(f'{ch_name}_bandwidth_limit', 'Unknown')
                coupling = config.get(f'{ch_name}_coupling', 'Unknown')
                offset = config.get(f'{ch_name}_offset', 'Unknown')
                display = config.get(f'{ch_name}_display', 'Unknown')
                
                # Get custom channel label if available
                channel_key = f'CH{ch_num}'
                custom_label = self.channel_metadata.get(channel_key, {}).get('label', '')
                channel_color = channel_colors.get(channel_key, '#cccccc')
                
                channel_configs.append(f'''
                <div class="channel-tile">
                    <div class="channel-banner" style="background-color: {channel_color};">
                        <h4>Channel-{ch_num}</h4>
                    </div>
                    <div class="channel-content">
                        <p><strong>Label:</strong> {custom_label or 'None'}</p>
                        <p><strong>Voltage Scale:</strong> {scale}</p>
                        <p><strong>Bandwidth Limit:</strong> {bandwidth}</p>
                        <p><strong>Coupling:</strong> {coupling}</p>
                        <p><strong>Offset:</strong> {offset}</p>
                    </div>
                </div>
                ''')
        
        # Check for Math channel
        if 'M1' in self.channel_data:
            custom_label = self.channel_metadata.get('M1', {}).get('label', '')
            channel_color = channel_colors.get('M1', '#cccccc')
            
            channel_configs.append(f'''
            <div class="channel-tile">
                <div class="channel-banner" style="background-color: {channel_color};">
                    <h4>Math-1</h4>
                </div>
                <div class="channel-content">
                    <p><strong>Label:</strong> {custom_label or 'None'}</p>
                    <p><strong>Function:</strong> Math function (details from oscilloscope)</p>
                </div>
            </div>
            ''')
        
        # Default to CH1 if no channels found
        if not channel_configs:
            scale = config.get('ch1_scale', 'Unknown')
            bandwidth = config.get('ch1_bandwidth_limit', 'Unknown') 
            coupling = config.get('ch1_coupling', 'Unknown')
            offset = config.get('ch1_offset', 'Unknown')
            
            # Get custom CH1 label if available
            custom_label = self.channel_metadata.get('CH1', {}).get('label', '')
            channel_color = channel_colors.get('CH1', '#cccccc')
            
            channel_configs.append(f'''
            <div class="channel-tile">
                <div class="channel-banner" style="background-color: {channel_color};">
                    <h4>Channel-1</h4>
                </div>
                <div class="channel-content">
                    <p><strong>Label:</strong> {custom_label or 'None'}</p>
                    <p><strong>Voltage Scale:</strong> {scale}</p>
                    <p><strong>Bandwidth Limit:</strong> {bandwidth}</p>
                    <p><strong>Coupling:</strong> {coupling}</p>
                    <p><strong>Offset:</strong> {offset}</p>
                </div>
            </div>
            ''')
        
        return '<div class="channel-tiles-container">' + ''.join(channel_configs) + '</div>'
    
    def create_all_plots_html(self):
        """Create HTML for all available channel plots."""
        plots_html = []
        
        # Generate plots for all available channels
        for channel in sorted(self.channel_data.keys()):
            plot_html = self.create_channel_plot(channel)
            plots_html.append(f'''
            <div class="plot-section">
                <h3>{channel} Waveform</h3>
                {plot_html}
            </div>
            ''')
        
        return ''.join(plots_html)
    
    def create_csv_data_section(self):
        """Create HTML section with embedded CSV data for download."""
        if not self.csv_data_b64:
            return ""
            
        csv_section = """
        <div class="csv-data-section">
            <h3>Raw Data Files</h3>
            <p>The following CSV data files are embedded in this report and can be downloaded:</p>
            <div class="csv-downloads">
        """
        
        for channel, csv_b64 in self.csv_data_b64.items():
            # Create filename based on channel
            filename = f"{channel.lower()}_waveform_data.csv"
            csv_section += f"""
                <div class="csv-download-item">
                    <h4>{channel} Waveform Data</h4>
                    <p>Contains {len(self.channel_data[channel])} data points</p>
                    <a href="data:text/csv;base64,{csv_b64}" 
                       download="{filename}" 
                       class="download-btn">
                        📊 Download {channel} CSV Data
                    </a>
                </div>
            """
        
        csv_section += """
            </div>
        </div>
        """
        
        return csv_section

    def create_notes_section_html(self):
        """Create HTML section for measurement notes."""
        if not self.measurement_notes_html or self.measurement_notes_html.strip() == "":
            return ""  # Don't show notes section if no notes exist
        
        # Fix image paths to use the copied images in the images/ directory
        # This converts /temp/filename.png to ./images/filename.png for the report
        import re
        fixed_notes_html = re.sub(
            r'src="/temp/([^"]+)"',
            r'src="./images/\1"',
            self.measurement_notes_html
        )
        
        notes_section = f"""
        <div class="notes-section">
            <h3>📝 Measurement Notes</h3>
            <div class="notes-content">
                {fixed_notes_html}
            </div>
        </div>
        """
        
        return notes_section

    def generate_html_report(self, output_file: str = "measurement_report.html"):
        """Generate the static HTML report."""
        
        # Get directory name for title
        directory_name = self.input_dir.name
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oscilloscope Measurement Report</title>
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
        .csv-data-section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 30px 0;
        }}
        .csv-downloads {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .channel-tiles-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .channel-tile {{
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            background-color: white;
        }}
        .channel-banner {{
            padding: 15px;
            color: black;
            font-weight: bold;
            text-align: center;
            border-bottom: 1px solid #ddd;
        }}
        .channel-banner h4 {{
            margin: 0;
            font-size: 1.1em;
            color: black;
            text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
        }}
        .channel-content {{
            padding: 15px;
        }}
        .channel-content p {{
            margin: 8px 0;
            font-size: 0.9em;
        }}
        .channel-content strong {{
            color: #495057;
            margin-top: 15px;
        }}
        .csv-download-item {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        .csv-download-item h4 {{
            margin-top: 0;
            color: #495057;
        }}
        .download-btn {{
            display: inline-block;
            background-color: #28a745;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
            transition: background-color 0.3s;
        }}
        .download-btn:hover {{
            background-color: #218838;
        }}
        .notes-section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #1f77b4;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .notes-section h3 {{
            margin-top: 0;
            color: #1f77b4;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .notes-content {{
            margin-top: 15px;
            line-height: 1.6;
        }}
        .notes-content img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .notes-content h1, .notes-content h2, .notes-content h3 {{
            color: #495057;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .notes-content p {{
            margin-bottom: 12px;
        }}
        .notes-content code {{
            background-color: #e9ecef;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .notes-content pre {{
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{directory_name}</h1>
            <h2>Measurement Report</h2>
        </div>
        
        {notes_section}
        
        <div class="info-section">
            <h3>Test Information</h3>
            <p><strong>Instrument:</strong> Keysight MSOX4154A Oscilloscope</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>Statistics Mode:</strong> {statistics_mode}</p>
            <p><strong>Input Directory:</strong> {input_dir}</p>
            <p><strong>Raw Response:</strong> <code>{raw_response}</code></p>
        </div>
        
        <div class="info-section">
            <h3>Oscilloscope Configuration</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div>
                    <h4>Acquisition Settings</h4>
                    <p><strong>Acquisition Mode:</strong> {acquisition_mode}</p>
                    <p><strong>Time Scale:</strong> {time_scale}</p>
                </div>
                {channel_configs}
            </div>
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
            
            {all_plots}
        </div>
        
        {csv_data_section}
        
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
        
        # Generate dynamic content
        channel_configs_html = self.create_channel_config_html()
        all_plots_html = self.create_all_plots_html()
        csv_data_section_html = self.create_csv_data_section()
        notes_section_html = self.create_notes_section_html()
        
        # Fill template
        html_content = html_template.format(
            directory_name=directory_name,
            timestamp=self.measurement_data.get('timestamp', 'Unknown'),
            statistics_mode=self.measurement_data.get('statistics_mode', 'Unknown'),
            input_dir=str(self.input_dir),
            raw_response=self.measurement_data.get('raw_response', ''),
            acquisition_mode=self.measurement_data.get('config', {}).get('acquisition_mode', 'Unknown'),
            time_scale=self.measurement_data.get('config', {}).get('time_scale', 'Unknown'),
            channel_configs=channel_configs_html,
            measurements_rows=measurements_rows,
            screenshot_section=screenshot_section,
            all_plots=all_plots_html,
            csv_data_section=csv_data_section_html,
            notes_section=notes_section_html,
            generation_time=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Write HTML file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
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