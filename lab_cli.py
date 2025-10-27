#!/usr/bin/env python3
"""
Lab Data Logging CLI API - Backdoor Testing Interface

This script provides a command-line interface to all the functionality
available in the web GUI, designed for testing and automation purposes.

Features:
- Run measurement captures with full configuration
- Generate HTML reports from captured data
- List and manage test results
- Validate configuration files
- Batch processing capabilities

Usage:
    python lab_cli.py run-test --help
    python lab_cli.py generate-report --help
    python lab_cli.py list-results --help

Author: Redlen Technologies Lab Automation Team
Date: 2025-10
"""

import sys
import os
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import logging
import asyncio
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure the virtual environment is activated
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
if os.name == "nt":
    venv_python = os.path.join(venv_path, "Scripts", "python.exe")
else:
    venv_python = os.path.join(venv_path, "bin", "python3")

if os.path.exists(venv_python):
    PYTHON_EXE = venv_python
else:
    PYTHON_EXE = sys.executable

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
            "CH1": True,
            "CH2": False,
            "CH3": False,
            "CH4": False,
            "M1": True
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
            with open(defaults_file, 'r') as f:
                loaded_defaults = yaml.safe_load(f) or {}
                defaults.update(loaded_defaults)
        except Exception as e:
            logger.error(f"Error loading defaults.yml: {e}")
    else:
        logger.info("defaults.yml not found, using built-in defaults")
    
    return defaults

def save_config_to_file(config: Dict[str, Any], filepath: str) -> bool:
    """Save configuration to a YAML file."""
    try:
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        logger.info(f"Configuration saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to {filepath}: {e}")
        return False

def load_config_from_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load configuration from a YAML file."""
    try:
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {filepath}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {filepath}: {e}")
        return None

def build_output_dir(destination: str, board_number: str, label: str, auto_timestamp: bool, timestamp_format: str) -> str:
    """Build the output directory path."""
    output_dir = destination
    
    if auto_timestamp:
        now = datetime.now()
        if timestamp_format == "YYYYMMDD.HHMMSS":
            timestamp = now.strftime("%Y%m%d.%H%M%S")
        else:  # YYYYMMDD_HHMMSS
            timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Build directory name: Board_Label_Timestamp
        dir_name = f"{board_number}_{label}_{timestamp}"
    else:
        # Build directory name: Board_Label
        dir_name = f"{board_number}_{label}"
    
    output_dir = os.path.join(destination, dir_name)
    return output_dir

async def run_measurement_capture(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the measurement capture process."""
    logger.info("=== MEASUREMENT CAPTURE STARTED ===")
    logger.info(f"Config: {json.dumps(config, indent=2)}")
    
    try:
        # Get active channels
        active_channels = [ch for ch, enabled in config.get("channels", {}).items() if enabled]
        capture_types = [ct for ct, enabled in config.get("capture_types", {}).items() if enabled]
        
        logger.info(f"Active channels: {active_channels}")
        logger.info(f"Capture types: {capture_types}")
        
        # Build command
        cmd = [
            PYTHON_EXE, "test_measurement_results.py",
            config["visa_address"],
            "--output-dir", config["output_dir"]
        ]
        
        # Add channel options
        for channel in active_channels:
            cmd.extend(["--channel", channel])
                
        # Add capture type options
        if "screenshot" not in capture_types:
            cmd.append("--no-screenshot")
        if "waveforms" not in capture_types:
            cmd.append("--no-waveforms")
        
        logger.info(f"Command to execute: {' '.join(cmd)}")
        
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
        
        logger.info("=== SUBPROCESS STDOUT ===")
        logger.info(stdout_text)
        
        if stderr_text:
            logger.error("=== SUBPROCESS STDERR ===")
            logger.error(stderr_text)
        
        if process.returncode == 0:
            logger.info("Measurement capture completed successfully")
            
            # Generate HTML report if requested
            if "html_report" in capture_types:
                logger.info("Generating HTML report...")
                
                report_cmd = [
                    PYTHON_EXE, "generate_static_report.py",
                    config["output_dir"],
                    "--output", os.path.join(config["output_dir"], "measurement_report.html")
                ]
                
                logger.info(f"Report command: {' '.join(report_cmd)}")
                
                report_process = await asyncio.create_subprocess_exec(
                    *report_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.getcwd()
                )
                
                report_stdout, report_stderr = await report_process.communicate()
                
                report_stdout_text = report_stdout.decode('utf-8', errors='replace')
                report_stderr_text = report_stderr.decode('utf-8', errors='replace')
                
                logger.info("=== REPORT GENERATION STDOUT ===")
                logger.info(report_stdout_text)
                
                if report_stderr_text:
                    logger.error("=== REPORT GENERATION STDERR ===")
                    logger.error(report_stderr_text)
                
                if report_process.returncode == 0:
                    logger.info("HTML report generated successfully")
                else:
                    logger.error(f"HTML report generation failed with return code: {report_process.returncode}")
            
            return {
                "success": True,
                "output_dir": config["output_dir"],
                "stdout": stdout_text,
                "stderr": stderr_text
            }
        else:
            error_msg = f"Measurement capture failed with return code: {process.returncode}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "stdout": stdout_text,
                "stderr": stderr_text
            }
            
    except Exception as e:
        error_msg = f"Unexpected error in run_measurement_capture: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": error_msg}

def list_results(results_dir: str = "captures") -> List[Dict[str, Any]]:
    """List all available test results."""
    results_dir = Path(results_dir)
    results = []
    
    if not results_dir.exists():
        logger.warning(f"Results directory {results_dir} does not exist")
        return results
    
    # Look for directories with timestamp patterns
    for item in results_dir.iterdir():
        if item.is_dir():
            result_info = {
                "name": item.name,
                "path": str(item),
                "created": datetime.fromtimestamp(item.stat().st_ctime).isoformat(),
                "files": []
            }
            
            # Look for common files
            for pattern in ["*.txt", "*.png", "*.csv", "*.html"]:
                files = list(item.glob(pattern))
                result_info["files"].extend([f.name for f in files])
            
            results.append(result_info)
    
    # Sort by creation time, newest first
    results.sort(key=lambda x: x["created"], reverse=True)
    return results

def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    # Required fields
    required_fields = ["visa_address", "destination", "board_number", "label"]
    for field in required_fields:
        if field not in config:
            issues.append(f"Missing required field: {field}")
    
    # Channels validation
    if "channels" in config:
        valid_channels = {"CH1", "CH2", "CH3", "CH4", "M1"}
        for channel in config["channels"]:
            if channel not in valid_channels:
                issues.append(f"Invalid channel: {channel}")
    
    # Capture types validation
    if "capture_types" in config:
        valid_capture_types = {"measurements", "waveforms", "screenshot", "config", "html_report"}
        for capture_type in config["capture_types"]:
            if capture_type not in valid_capture_types:
                issues.append(f"Invalid capture type: {capture_type}")
    
    # Check if at least one channel is enabled
    if "channels" in config and not any(config["channels"].values()):
        issues.append("At least one channel must be enabled")
    
    # Check if at least one capture type is enabled
    if "capture_types" in config and not any(config["capture_types"].values()):
        issues.append("At least one capture type must be enabled")
    
    return issues

async def cmd_run_test(args):
    """Run a measurement test."""
    print("Lab Data Logging CLI - Run Test")
    print("=" * 40)
    
    # Load base configuration
    if args.config:
        config = load_config_from_file(args.config)
        if not config:
            print(f"Error: Could not load configuration from {args.config}")
            return 1
    else:
        config = load_defaults()
    
    # Override with command line arguments
    if args.visa_address:
        config["visa_address"] = args.visa_address
    if args.destination:
        config["destination"] = args.destination
    if args.board_number:
        config["board_number"] = args.board_number
    if args.label:
        config["label"] = args.label
    
    # Handle channels
    if args.channels:
        # Disable all channels first
        for ch in config["channels"]:
            config["channels"][ch] = False
        # Enable specified channels
        for ch in args.channels:
            if ch in config["channels"]:
                config["channels"][ch] = True
    
    # Handle capture types
    if args.capture_types:
        # Disable all capture types first
        for ct in config["capture_types"]:
            config["capture_types"][ct] = False
        # Enable specified capture types
        for ct in args.capture_types:
            if ct in config["capture_types"]:
                config["capture_types"][ct] = True
    
    # Handle boolean flags
    if args.no_timestamp:
        config["auto_timestamp"] = False
    if args.timestamp_format:
        config["timestamp_format"] = args.timestamp_format
    
    # Validate configuration
    issues = validate_config(config)
    if issues:
        print("Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    
    # Build output directory
    config["output_dir"] = build_output_dir(
        config["destination"],
        config["board_number"],
        config["label"],
        config["auto_timestamp"],
        config["timestamp_format"]
    )
    
    print(f"Configuration:")
    print(f"  VISA Address: {config['visa_address']}")
    print(f"  Output Directory: {config['output_dir']}")
    print(f"  Board Number: {config['board_number']}")
    print(f"  Label: {config['label']}")
    print(f"  Active Channels: {[ch for ch, enabled in config['channels'].items() if enabled]}")
    print(f"  Capture Types: {[ct for ct, enabled in config['capture_types'].items() if enabled]}")
    print()
    
    # Save configuration if requested
    if args.save_config:
        save_config_to_file(config, args.save_config)
    
    # Create output directory
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    # Run the test
    print("Starting measurement capture...")
    result = await run_measurement_capture(config)
    
    if result["success"]:
        print("SUCCESS: Measurement capture completed successfully!")
        print(f"Results saved to: {result['output_dir']}")
        return 0
    else:
        print("ERROR: Measurement capture failed!")
        print(f"Error: {result['error']}")
        return 1

def cmd_list_results(args):
    """List available test results."""
    print("Lab Data Logging CLI - Test Results")
    print("=" * 40)
    
    results = list_results(args.results_dir)
    
    if not results:
        print("No test results found.")
        return 0
    
    print(f"Found {len(results)} test result(s):")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}")
        print(f"   Created: {result['created']}")
        print(f"   Path: {result['path']}")
        print(f"   Files: {', '.join(result['files'][:5])}")
        if len(result['files']) > 5:
            print(f"          ... and {len(result['files']) - 5} more files")
        print()
    
    return 0

def cmd_generate_report(args):
    """Generate HTML report from test results."""
    print("Lab Data Logging CLI - Generate Report")
    print("=" * 40)
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return 1
    
    if not args.output:
        args.output = input_dir / "measurement_report.html"
    
    print(f"Input Directory: {input_dir}")
    print(f"Output File: {args.output}")
    print()
    
    # Build command
    cmd = [
        PYTHON_EXE, "generate_static_report.py",
        str(input_dir),
        "--output", str(args.output)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    # Run the report generation
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        print("=== REPORT GENERATION OUTPUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== REPORT GENERATION ERRORS ===")
            print(result.stderr)
        
        if result.returncode == 0:
            print("SUCCESS: HTML report generated successfully!")
            print(f"Report saved to: {args.output}")
            return 0
        else:
            print("ERROR: HTML report generation failed!")
            print(f"Return code: {result.returncode}")
            return 1
            
    except Exception as e:
        print(f"Error running report generation: {e}")
        return 1

def cmd_validate_config(args):
    """Validate a configuration file."""
    print("Lab Data Logging CLI - Validate Configuration")
    print("=" * 40)
    
    if not Path(args.config).exists():
        print(f"Error: Configuration file {args.config} does not exist")
        return 1
    
    config = load_config_from_file(args.config)
    if not config:
        print(f"Error: Could not load configuration from {args.config}")
        return 1
    
    print(f"Configuration file: {args.config}")
    print()
    
    issues = validate_config(config)
    
    if not issues:
        print("SUCCESS: Configuration is valid!")
        print()
        print("Configuration summary:")
        print(f"  VISA Address: {config.get('visa_address', 'Not set')}")
        print(f"  Destination: {config.get('destination', 'Not set')}")
        print(f"  Board Number: {config.get('board_number', 'Not set')}")
        print(f"  Label: {config.get('label', 'Not set')}")
        print(f"  Active Channels: {[ch for ch, enabled in config.get('channels', {}).items() if enabled]}")
        print(f"  Capture Types: {[ct for ct, enabled in config.get('capture_types', {}).items() if enabled]}")
        return 0
    else:
        print("X Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Lab Data Logging CLI API - Backdoor Testing Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a basic test with defaults
  python lab_cli.py run-test
  
  # Run test with specific configuration
  python lab_cli.py run-test --visa-address "USB0::0x0957::0x17BC::MY56310625::INSTR" --channels CH1 CH2 --board-number 00002
  
  # Run test from configuration file
  python lab_cli.py run-test --config my_test_config.yml
  
  # List all test results
  python lab_cli.py list-results
  
  # Generate report from existing data
  python lab_cli.py generate-report ./captures/00001_Test_20251002.143000
  
  # Validate configuration file
  python lab_cli.py validate-config my_test_config.yml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run test command
    run_parser = subparsers.add_parser('run-test', help='Run a measurement test')
    run_parser.add_argument('--config', help='Configuration file to load (YAML format)')
    run_parser.add_argument('--visa-address', help='VISA address of the oscilloscope')
    run_parser.add_argument('--destination', help='Base destination directory for results')
    run_parser.add_argument('--board-number', help='Board number for naming')
    run_parser.add_argument('--label', help='Test label for naming')
    run_parser.add_argument('--channels', nargs='+', choices=['CH1', 'CH2', 'CH3', 'CH4', 'M1'], 
                          help='Channels to capture (space-separated)')
    run_parser.add_argument('--capture-types', nargs='+', 
                          choices=['measurements', 'waveforms', 'screenshot', 'config', 'html_report'],
                          help='Types of data to capture (space-separated)')
    run_parser.add_argument('--no-timestamp', action='store_true', help='Disable automatic timestamping')
    run_parser.add_argument('--timestamp-format', choices=['YYYYMMDD.HHMMSS', 'YYYYMMDD_HHMMSS'], 
                          help='Timestamp format')
    run_parser.add_argument('--save-config', help='Save final configuration to file')
    
    # List results command
    list_parser = subparsers.add_parser('list-results', help='List available test results')
    list_parser.add_argument('--results-dir', default='captures', help='Directory to search for results')
    
    # Generate report command
    report_parser = subparsers.add_parser('generate-report', help='Generate HTML report from test data')
    report_parser.add_argument('input_dir', help='Directory containing test data')
    report_parser.add_argument('--output', help='Output HTML file path')
    
    # Validate config command
    validate_parser = subparsers.add_parser('validate-config', help='Validate a configuration file')
    validate_parser.add_argument('config', help='Configuration file to validate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'run-test':
            return asyncio.run(cmd_run_test(args))
        elif args.command == 'list-results':
            return cmd_list_results(args)
        elif args.command == 'generate-report':
            return cmd_generate_report(args)
        elif args.command == 'validate-config':
            return cmd_validate_config(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())