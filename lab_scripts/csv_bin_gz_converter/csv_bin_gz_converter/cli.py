"""
Command-line interface for CSV to BIN.GZ Converter
"""

import argparse
import sys
from .launcher import launch_app

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="csv-bin-gz-converter",
        description="Launch the CSV to BIN.GZ Converter desktop application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  csv-bin-gz-converter              # Launch the app normally
  csv-bin-gz-converter --debug      # Launch with debug output
  csv-bin-gz-converter -h           # Show this help message
        """.strip()
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug output"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="csv-bin-gz-converter 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Launch the Electron app
    exit_code = launch_app(debug=args.debug)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
