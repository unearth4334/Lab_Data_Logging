#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for lockout hysteresis test.
"""

import argparse
from colorama import Fore

from .test import run_lockout_test, hdr, warn, ok, err

# Default values
V_START = 10.0
V_END = 14.0
V_STEP = 0.005
CURRENT_LIMIT_A = 2.0
SETTLE_S = 0.05


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "UV/OV lockout hysteresis test – sweeps DP711 voltage and "
            "records DMM6500 readings to characterise latching thresholds."
        )
    )

    mode_grp = parser.add_mutually_exclusive_group()
    mode_grp.add_argument("--auto",     action="store_true",
                          help="Replace Enter breakpoints with 1-second delays")
    mode_grp.add_argument("--no-debug", action="store_true",
                          help="Disable all breakpoints and pauses (fully automated)")

    parser.add_argument("--com",     type=str,   default=None,
                        help="COM port for DP711 (e.g. COM15).  Prompts if omitted.")
    parser.add_argument("--start",   type=float, default=V_START,
                        help=f"Sweep start voltage in V (default: {V_START})")
    parser.add_argument("--end",     type=float, default=V_END,
                        help=f"Sweep end voltage in V (default: {V_END})")
    parser.add_argument("--step",    type=float, default=V_STEP,
                        help=f"Step size in V (default: {V_STEP})")
    parser.add_argument("--settle",  type=float, default=SETTLE_S,
                        help=f"Settling delay per step in seconds (default: {SETTLE_S})")
    parser.add_argument("--current", type=float, default=CURRENT_LIMIT_A,
                        help=f"DP711 current limit in A (default: {CURRENT_LIMIT_A})")

    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()

    if args.no_debug:
        mode = "off"
    elif args.auto:
        mode = "auto"
    else:
        mode = "debug"

    try:
        run_lockout_test(
            v_start=args.start,
            v_end=args.end,
            v_step=args.step,
            settle_s=args.settle,
            current_limit_a=args.current,
            mode=mode,
            com_port=args.com,
        )
    except KeyboardInterrupt:
        hdr("TEST ABORTED BY USER", color=Fore.RED)
        warn("Test interrupted by user.")
    except Exception as exc:
        hdr("TEST FAILED", color=Fore.RED)
        err(str(exc))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
