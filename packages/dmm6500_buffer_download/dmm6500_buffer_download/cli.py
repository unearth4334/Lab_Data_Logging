#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for DMM6500 buffer download tool.
"""

import argparse
import sys

from .download import download_buffer, print_error


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Download buffer data from DMM6500 digital multimeter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --ip 169.254.233.96 -m "Voltage test"
  %(prog)s --address "USB0::0x05E6::0x6500::04492372::INSTR" --plot
  %(prog)s --buffer defbuffer1 --output my_data.csv
        """
    )
    
    # Connection options
    parser.add_argument('--ip', type=str, help='IP address for ethernet connection')
    parser.add_argument('--address', type=str, help='Full VISA resource string')
    
    # Buffer and output options
    parser.add_argument('--buffer', type=str, default='defbuffer1',
                        help='Buffer name to download (default: defbuffer1)')
    parser.add_argument('--output', type=str,
                        help='Output CSV filename (default: auto-generated in output/ directory)')
    parser.add_argument('-m', '--message', type=str,
                        help='Optional message/metadata to include in file header and filename')
    
    # Download options
    parser.add_argument('--chunk', type=int, default=50000,
                        help='Points per fetch operation (default: 50000)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable verbose SCPI logging')
    
    # Post-processing options
    parser.add_argument('--plot', action='store_true',
                        help='Plot the downloaded data after saving')
    
    args = parser.parse_args()
    
    try:
        download_buffer(
            buffer_name=args.buffer,
            output_file=args.output,
            ip_address=args.ip,
            visa_address=args.address,
            message=args.message,
            chunk_size=args.chunk,
            debug=args.debug,
            show_plot=args.plot
        )
        return 0
    except KeyboardInterrupt:
        print_error("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print_error(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
