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
        
        # Create index.html redirect
        index_file = output_dir / "index.html"
        with open(index_file, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lab Data Logging - API Documentation</title>
    <meta http-equiv="refresh" content="0; url=data_logger.html">
    <style>
        body {
            font-family: sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        h1 { color: #2c3e50; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .module-list {
            list-style: none;
            padding: 0;
        }
        .module-list li {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <h1>Lab Data Logging - API Documentation</h1>
    <p>Redirecting to main documentation...</p>
    <p>If not redirected, please select a module:</p>
    <ul class="module-list">
        <li><a href="data_logger.html">data_logger - Main Data Logger</a></li>
        <li><a href="libs/DMM6500.html">DMM6500 - Keithley DMM6500 Multimeter</a></li>
        <li><a href="libs/Keysight34460A.html">Keysight34460A - Keysight 34460A Multimeter</a></li>
        <li><a href="libs/KeysightMSOX4154A.html">KeysightMSOX4154A - Keysight MSOX4154A Oscilloscope</a></li>
        <li><a href="libs/StanfordPS310.html">StanfordPS310 - Stanford PS310 High Voltage Power Supply</a></li>
        <li><a href="libs/RigolDP832.html">RigolDP832 - Rigol DP832 Power Supply</a></li>
        <li><a href="libs/RigolDS7034.html">RigolDS7034 - Rigol DS7034 Oscilloscope</a></li>
        <li><a href="libs/DL3021.html">DL3021 - Electronic Load</a></li>
        <li><a href="libs/FLUKE45.html">FLUKE45 - Fluke 45 Multimeter</a></li>
        <li><a href="libs/KA3010P.html">KA3010P - Power Supply</a></li>
        <li><a href="libs/KS33500B.html">KS33500B - Keysight 33500B Waveform Generator</a></li>
        <li><a href="libs/U1233A.html">U1233A - Handheld Multimeter</a></li>
        <li><a href="libs/DAC.html">DAC - Digital to Analog Converter</a></li>
        <li><a href="libs/EPS.html">EPS - Electronic Power Supply</a></li>
        <li><a href="libs/DP832.html">DP832 - Power Supply</a></li>
        <li><a href="libs/loading.html">loading - Loading Indicator Utilities</a></li>
    </ul>
</body>
</html>
""")
        
        print(f"\n✓ Index page created: {index_file}")
        print(f"\nDocumentation is available at: {output_dir}/index.html")
        print(f"Open in browser: file://{output_dir.absolute()}/index.html")
        
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
