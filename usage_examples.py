#!/usr/bin/env python3
"""
Simple usage examples for the DMM6500 resistance plotter.

This script demonstrates various ways to use the resistance_plotter.py script
and provides practical examples for different use cases.
"""

import subprocess
import sys
import time
import os

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def run_example(title, description, command, duration=10):
    """Run an example with proper formatting."""
    print_header(title)
    print(f"Description: {description}")
    print(f"Command: {command}")
    print(f"Duration: {duration} seconds")
    print()
    print("Running example...")
    print("-" * 40)
    
    try:
        # Run the command with timeout
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Read output line by line
            line = process.stdout.readline()
            if line:
                print(line.rstrip())
            
            # Check if process has finished
            if process.poll() is not None:
                break
                
            time.sleep(0.1)
        
        # Terminate if still running
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=2)
        
        print("-" * 40)
        print("Example completed.")
        
    except Exception as e:
        print(f"Error running example: {e}")
    
    print()

def main():
    """Run all examples."""
    print("DMM6500 Resistance Plotter - Usage Examples")
    print("=" * 60)
    print("This script demonstrates various ways to use the resistance plotter.")
    print("All examples run in demo mode (no hardware required).")
    
    examples = [
        {
            "title": "Basic Usage - Text Mode",
            "description": "Simple resistance measurements in text-only mode",
            "command": "python3 resistance_plotter.py --demo --no-gui --interval 1 --max-points 20",
            "duration": 8
        },
        {
            "title": "Fast Measurements",
            "description": "Rapid measurements every 0.5 seconds",
            "command": "python3 resistance_plotter.py --demo --no-gui --interval 0.5 --max-points 30",
            "duration": 10
        },
        {
            "title": "Help Documentation",
            "description": "Display help and available options",
            "command": "python3 resistance_plotter.py --help",
            "duration": 2
        },
        {
            "title": "Statistical Analysis Focus",
            "description": "Focused on collecting statistics for latest 10 measurements",
            "command": "python3 resistance_plotter.py --demo --no-gui --interval 0.8 --max-points 15",
            "duration": 12
        }
    ]
    
    try:
        for i, example in enumerate(examples, 1):
            print(f"\nExample {i}/{len(examples)}")
            run_example(**example)
            
            if i < len(examples):
                print("Press Enter to continue to next example...")
                input()
    
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    
    print_header("Summary")
    print("Key Features Demonstrated:")
    print("• Real-time resistance measurements from DMM6500")
    print("• Configurable measurement intervals")
    print("• Automatic statistics calculation for latest 10 measurements")
    print("• Text-based output suitable for headless environments")
    print("• Demo mode for testing without hardware")
    print("• Command-line interface with validation")
    print()
    print("For GUI mode with plotting (requires display):")
    print("  python3 resistance_plotter.py --demo --interval 2")
    print()
    print("For real hardware usage:")
    print("  python3 resistance_plotter.py --interval 1")
    print()

if __name__ == "__main__":
    main()