#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic API Documentation Generator

Generates comprehensive HTML documentation for the Lab Data Logging project
using pdoc3. This script automatically documents all device drivers in the
libs/ directory and the main data_logger.py module.

Usage:
    python scripts/generate_docs.py
    
Output:
    docs/api/  - HTML documentation for all modules
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Generate API documentation using pdoc3."""
    
    # Get repository root directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Define output directory
    output_dir = repo_root / "docs" / "api"
    
    # Modules to document
    modules = [
        "data_logger",
        "libs.DMM6500",
        "libs.Keysight34460A",
        "libs.KeysightMSOX4154A",
        "libs.StanfordPS310",
        "libs.RigolDP832",
        "libs.RigolDS7034",
        "libs.DL3021",
        "libs.FLUKE45",
        "libs.KA3010P",
        "libs.KS33500B",
        "libs.U1233A",
        "libs.DAC",
        "libs.EPS",
        "libs.DP832",
        "libs.loading"
    ]
    
    print("=" * 70)
    print("Lab Data Logging - Automatic API Documentation Generator")
    print("=" * 70)
    print(f"\nRepository root: {repo_root}")
    print(f"Output directory: {output_dir}")
    print(f"\nModules to document: {len(modules)}")
    
    # Change to repository root
    os.chdir(repo_root)
    
    # Set PYTHONPATH to include the repository root and libs directory
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{repo_root}:{repo_root / 'libs'}"
    
    # Build pdoc3 command
    cmd = [
        sys.executable, "-m", "pdoc",
        "--html",
        "--output-dir", str(output_dir),
        "--force",
        "--config", "show_source_code=True"
    ] + modules
    
    print(f"\nGenerating documentation...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        # Run pdoc3
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        
        print("✓ Documentation generated successfully!")
        print(f"\n{result.stdout}")
        
        # Create enhanced index.html with command counts
        index_file = output_dir / "index.html"
        with open(index_file, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lab Data Logging - API Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            max-width: 1000px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { 
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }
        a { 
            color: #3498db; 
            text-decoration: none; 
        }
        a:hover { 
            text-decoration: underline;
            color: #2980b9;
        }
        .quick-links {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .quick-links a {
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 8px 15px;
            background: #3498db;
            color: white;
            border-radius: 4px;
            font-weight: 500;
        }
        .quick-links a:hover {
            background: #2980b9;
            text-decoration: none;
        }
        .module-list {
            list-style: none;
            padding: 0;
        }
        .module-list li {
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .module-list li:hover {
            background: #f8f9fa;
        }
        .module-info {
            flex: 1;
        }
        .command-count {
            background: #3498db;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
            white-space: nowrap;
        }
        .instrument-type {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-left: 10px;
        }
        .summary-box {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 20px 0;
        }
        .summary-box strong {
            color: #2e7d32;
        }
    </style>
</head>
<body>
    <h1>Lab Data Logging - API Documentation</h1>
    
    <div class="quick-links">
        <strong>Quick Access:</strong><br>
        <a href="README.md" target="_blank">📋 Measurement Commands Reference</a>
        <a href="data_logger.html">📦 Main Data Logger</a>
    </div>

    <div class="summary-box">
        <strong>📊 Summary:</strong> 13 instruments with 61 total measurement commands documented<br>
        <strong>📖 See:</strong> <a href="README.md" target="_blank">README.md</a> for a complete list of all supported measurement commands by instrument
    </div>

    <h2>Main Module</h2>
    <ul class="module-list">
        <li>
            <div class="module-info">
                <a href="data_logger.html"><strong>data_logger</strong> - Main Data Logger</a>
                <span class="instrument-type">Core Framework</span>
            </div>
        </li>
    </ul>

    <h2>Instrument Drivers</h2>
    <ul class="module-list">
        <li>
            <div class="module-info">
                <a href="libs/DMM6500.html"><strong>DMM6500</strong> - Keithley DMM6500 Multimeter</a>
                <span class="instrument-type">Multimeter</span>
            </div>
            <span class="command-count">4 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/Keysight34460A.html"><strong>Keysight34460A</strong> - Keysight 34460A Multimeter</a>
                <span class="instrument-type">Multimeter</span>
            </div>
            <span class="command-count">3 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/KeysightMSOX4154A.html"><strong>KeysightMSOX4154A</strong> - Keysight MSOX4154A Oscilloscope</a>
                <span class="instrument-type">Oscilloscope</span>
            </div>
            <span class="command-count">9 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/StanfordPS310.html"><strong>StanfordPS310</strong> - Stanford PS310 High Voltage Power Supply</a>
                <span class="instrument-type">Power Supply</span>
            </div>
            <span class="command-count">3 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/RigolDP832.html"><strong>RigolDP832</strong> - Rigol DP832 Power Supply</a>
                <span class="instrument-type">Power Supply</span>
            </div>
            <span class="command-count">6 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/RigolDS7034.html"><strong>RigolDS7034</strong> - Rigol DS7034 Oscilloscope</a>
                <span class="instrument-type">Oscilloscope</span>
            </div>
            <span class="command-count">16 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/DL3021.html"><strong>DL3021</strong> - Electronic Load</a>
                <span class="instrument-type">Electronic Load</span>
            </div>
            <span class="command-count">4 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/FLUKE45.html"><strong>FLUKE45</strong> - Fluke 45 Multimeter</a>
                <span class="instrument-type">Multimeter</span>
            </div>
            <span class="command-count">1 command</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/KA3010P.html"><strong>KA3010P</strong> - Power Supply</a>
                <span class="instrument-type">Power Supply</span>
            </div>
            <span class="command-count">2 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/U1233A.html"><strong>U1233A</strong> - Handheld Multimeter</a>
                <span class="instrument-type">Multimeter</span>
            </div>
            <span class="command-count">2 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/DAC.html"><strong>DAC</strong> - Digital to Analog Converter</a>
                <span class="instrument-type">DAC/INA226</span>
            </div>
            <span class="command-count">6 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/EPS.html"><strong>EPS</strong> - Environmental Control System</a>
                <span class="instrument-type">Environmental</span>
            </div>
            <span class="command-count">3 commands</span>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/DP832.html"><strong>DP832</strong> - Power Supply</a>
                <span class="instrument-type">Power Supply</span>
            </div>
            <span class="command-count">2 commands</span>
        </li>
    </ul>

    <h2>Utilities</h2>
    <ul class="module-list">
        <li>
            <div class="module-info">
                <a href="libs/KS33500B.html"><strong>KS33500B</strong> - Keysight 33500B Waveform Generator</a>
                <span class="instrument-type">Waveform Generator</span>
            </div>
        </li>
        <li>
            <div class="module-info">
                <a href="libs/loading.html"><strong>loading</strong> - Loading Indicator Utilities</a>
                <span class="instrument-type">Utility</span>
            </div>
        </li>
    </ul>

    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">
    
    <p style="text-align: center; color: #7f8c8d; font-size: 0.9em;">
        For a complete list of all supported measurement commands, see <a href="README.md" target="_blank"><strong>README.md</strong></a>
    </p>
</body>
</html>
""")
        
        print(f"\n✓ Enhanced index page created: {index_file}")
        print(f"✓ README.md with measurement commands reference available at: {output_dir}/README.md")
        print(f"\nDocumentation is available at: {output_dir}/index.html")
        print(f"Open in browser: file://{output_dir.absolute()}/index.html")
        print(f"\nFeatures:")
        print(f"  - Command counts displayed for each instrument")
        print(f"  - Instrument types/categories visible")
        print(f"  - README.md with complete measurement commands reference")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating documentation:")
        print(f"\nSTDOUT:\n{e.stdout}")
        print(f"\nSTDERR:\n{e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
