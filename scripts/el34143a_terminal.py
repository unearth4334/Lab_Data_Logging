"""
el34143a_terminal.py
====================
Interactive SCPI terminal for the Keysight EL34143A DC Electronic Load.

Usage:
    python scripts/el34143a_terminal.py
    python scripts/el34143a_terminal.py --address USB0::0x0957::0x8C18::MY12345678::INSTR
    python scripts/el34143a_terminal.py --ip 192.168.1.100

Commands:
    Type any SCPI command and press Enter.
    Commands ending with '?' are queries  — the response is printed.
    Commands without '?'  are writes     — no response is expected.

Special shell commands (prefix with '.'):
    .help          Show this help
    .idn           Send *IDN? and print result
    .cls           Send *CLS  (clear status)
    .rst           Send *RST  (reset instrument)
    .opc           Send *OPC? (wait for operation complete)
    .errors        Read all errors from the error queue (SYST:ERR?)
    .timeout <ms>  Change VISA timeout  (e.g.  .timeout 10000)
    .q / .quit     Disconnect and exit
"""

import argparse
import sys
import os

# Allow running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from libs.KeysightEL34143A import KeysightEL34143A


BANNER = """
╔══════════════════════════════════════════════════════╗
║   Keysight EL34143A – Interactive SCPI Terminal      ║
║   Type a SCPI command and press Enter.               ║
║   Commands ending with '?' return a response.        ║
║   Type .help for shell commands, .quit to exit.      ║
╚══════════════════════════════════════════════════════╝
"""


def drain_errors(inst) -> list[str]:
    """Read all errors from the instrument error queue."""
    errors = []
    while True:
        try:
            resp = inst.query("SYST:ERR?").strip()
        except Exception as e:
            errors.append(f"<VISA error reading error queue: {e}>")
            break
        errors.append(resp)
        # Error queue is empty when it returns +0 or 0
        if resp.startswith("+0") or resp.startswith("0,"):
            break
    return errors


def run_terminal(load: KeysightEL34143A):
    print(BANNER)
    print(f"Connected  : {load.address}")
    print(f"IDN        : {load.get_idn()}\n")

    while True:
        try:
            raw = input("SCPI> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        # ── Shell meta-commands ───────────────────────────────────────────────
        if raw.startswith("."):
            parts = raw.split()
            cmd   = parts[0].lower()

            if cmd in (".q", ".quit", ".exit"):
                print("Disconnecting…")
                break

            elif cmd == ".help":
                print(__doc__)

            elif cmd == ".idn":
                print(load.instrument.query("*IDN?").strip())

            elif cmd == ".cls":
                load.instrument.write("*CLS")
                print("*CLS sent.")

            elif cmd == ".rst":
                load.instrument.write("*RST")
                print("*RST sent.")

            elif cmd == ".opc":
                r = load.instrument.query("*OPC?").strip()
                print(f"*OPC? → {r}")

            elif cmd == ".errors":
                errs = drain_errors(load.instrument)
                for e in errs:
                    print(f"  {e}")

            elif cmd == ".timeout":
                if len(parts) < 2:
                    print(f"Current timeout: {load.instrument.timeout} ms")
                else:
                    try:
                        ms = int(parts[1])
                        load.instrument.timeout = ms
                        print(f"Timeout set to {ms} ms")
                    except ValueError:
                        print("Usage: .timeout <milliseconds>")

            else:
                print(f"Unknown shell command '{raw}'.  Type .help for help.")

            continue

        # ── SCPI command ──────────────────────────────────────────────────────
        is_query = "?" in raw

        try:
            if is_query:
                response = load.instrument.query(raw).strip()
                print(f"  → {response}")
            else:
                load.instrument.write(raw)
                # Optionally auto-check for errors after every write:
                # errs = drain_errors(load.instrument)
                # if not errs[0].startswith("+0"):
                #     for e in errs:
                #         print(f"  [ERR] {e}")
        except Exception as e:
            print(f"  [VISA ERROR] {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive SCPI terminal for Keysight EL34143A"
    )
    parser.add_argument("--address", help="Explicit VISA resource address")
    parser.add_argument("--ip",      help="IP address for Ethernet connection")
    parser.add_argument("--debug",   action="store_true", help="Enable driver debug output")
    args = parser.parse_args()

    try:
        load = KeysightEL34143A(
            address=args.address,
            ip_address=args.ip,
            debug=args.debug,
        )
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    try:
        run_terminal(load)
    finally:
        try:
            load.instrument.close()
            print("VISA session closed.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
