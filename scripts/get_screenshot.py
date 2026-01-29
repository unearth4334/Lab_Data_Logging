#!/usr/bin/env python3
"""
Simple screenshot capture script for Keysight MSOX4154A.

Usage:
    python scripts/get_screenshot.py OUTPUT_FILE [--visa-address VISA_ADDRESS]

Examples:
    python scripts/get_screenshot.py captures/scope.png
    python scripts/get_screenshot.py captures/scope.png --visa-address "USB0::0x0957::0x17BC::MY56310625::INSTR"
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.append(".")
from libs.KeysightMSOX4154A import KeysightMSOX4154A


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture a screenshot from a Keysight MSOX4154A oscilloscope."
    )
    parser.add_argument(
        "output_file",
        help="Output filename for the screenshot (e.g., captures/scope.png)"
    )
    parser.add_argument(
        "--visa-address",
        help="Optional VISA address (auto-detect if not provided)"
    )

    args = parser.parse_args()

    output_path = Path(args.output_file)
    if output_path.parent:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    osc = None
    try:
        if args.visa_address:
            osc = KeysightMSOX4154A(auto_connect=False)
            osc.connect(args.visa_address)
        else:
            osc = KeysightMSOX4154A()

        success = osc.save_screenshot(str(output_path), inksaver=False)
        return 0 if success else 1
    except Exception as exc:
        print(f"Screenshot failed: {exc}")
        return 1
    finally:
        if osc is not None:
            try:
                osc.disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
