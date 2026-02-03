#!/usr/bin/env python3
"""
enter-triggered-dmm.py

Menu-driven single-shot resistance capture for DMM6500.

Usage:
    python scripts/enter-triggered-dmm.py

Flow:
  1) Menu-select VISA address (auto-discovered if pyvisa is installed)
     - or manually type an address
  2) Menu-select resistance range (or auto)
  3) Press ENTER -> wait 10s -> take ONE measurement -> copy to clipboard
  4) Repeat until Ctrl+C

Uses project drivers:
    from libs.DMM6500 import DMM6500
"""

import asyncio
import sys
import time
from datetime import datetime

# Add project root to path for imports
sys.path.append(".")

from libs.DMM6500 import DMM6500
from libs.U1233A import U1233A

ANSI_REV = "\x1b[7m"
ANSI_RESET = "\x1b[0m"


# ---------- Clipboard ----------
def copy_to_clipboard(text: str) -> bool:
    """
    Robust clipboard copy:
      1) pyperclip (if installed)
      2) platform clipboard utilities (pbcopy/wl-copy/xclip/xsel/clip)
      3) tkinter fallback

    Returns True on success.
    """
    import platform
    import shutil
    import subprocess

    # 1) pyperclip
    try:
        import pyperclip  # type: ignore
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    # Helper to run a command and pipe text to stdin
    def _pipe(cmd: list[str]) -> bool:
        try:
            p = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return p.returncode == 0
        except Exception:
            return False

    sysname = platform.system().lower()

    # 2) platform utilities
    if sysname == "darwin":
        if shutil.which("pbcopy") and _pipe(["pbcopy"]):
            return True

    elif sysname == "windows":
        # cmd.exe clip
        if shutil.which("clip") and _pipe(["clip"]):
            return True
        # PowerShell fallback
        if shutil.which("powershell"):
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
                    ],
                    input=text.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                return True
            except Exception:
                pass

    else:
        # Linux / BSD
        # Wayland
        if shutil.which("wl-copy") and _pipe(["wl-copy"]):
            return True
        # X11
        if shutil.which("xclip") and _pipe(["xclip", "-selection", "clipboard"]):
            return True
        if shutil.which("xsel") and _pipe(["xsel", "--clipboard", "--input"]):
            return True

    # 3) tkinter last (often fails on headless)
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
        return True
    except Exception:
        return False


# ---------- VISA discovery ----------
def discover_visa_resources():
    """
    Best-effort VISA resource discovery via pyvisa.
    Returns list[str]. Returns [] if pyvisa not installed / no backend.
    """
    try:
        import pyvisa  # type: ignore
    except Exception:
        return []

    try:
        rm = pyvisa.ResourceManager()
    except Exception:
        return []

    try:
        resources = list(rm.list_resources())
        return resources
    except Exception:
        return []
    finally:
        try:
            rm.close()
        except Exception:
            pass


def discover_serial_ports():
    """
    Best-effort serial port discovery via pyserial.
    Returns list of (device, description) tuples. Returns [] on failure.
    """
    try:
        import serial.tools.list_ports
    except Exception:
        return []

    try:
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]
    except Exception:
        return []


# ---------- Menus ----------
def _print_menu(title: str, items: list[str]):
    print()
    print(title)
    for i, it in enumerate(items, start=1):
        print(f"  {i:2d}) {it}")


def prompt_menu(title: str, items: list[str], *, allow_custom: bool = False, custom_label: str = "Enter manually"):
    """
    Returns selected item (string).
    If allow_custom=True, adds an extra menu option to type a custom string.
    """
    menu_items = list(items)
    if allow_custom:
        menu_items.append(custom_label)

    while True:
        _print_menu(title, menu_items)
        raw = input("\nSelect an option: ").strip()
        if not raw:
            continue
        if not raw.isdigit():
            print("Please enter a number.")
            continue

        idx = int(raw)
        if idx < 1 or idx > len(menu_items):
            print("Out of range.")
            continue

        choice = menu_items[idx - 1]
        if allow_custom and choice == custom_label:
            val = input("Type the address: ").strip()
            if val:
                return val
            print("Address cannot be empty.")
            continue

        return choice


def parse_range_text(txt: str):
    t = txt.strip().lower()
    if t == "auto":
        return "auto"
    mult = 1.0
    if t.endswith("k"):
        mult = 1_000.0
        t = t[:-1]
    elif t.endswith("m"):
        mult = 1_000_000.0
        t = t[:-1]
    return float(t) * mult


# ---------- Async UI helpers ----------
async def wait_for_enter(prompt: str = "Press ENTER to arm a capture (Ctrl+C to quit)… "):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    await asyncio.to_thread(sys.stdin.readline)


async def countdown(seconds: float, label: str = "Arming", flash_hz: float = 4.0):
    width = 40
    start = time.monotonic()
    end = start + max(0.0, float(seconds))

    invert = False
    next_toggle = end - 1.0
    flash_period = 1.0 / flash_hz if flash_hz and flash_hz > 0 else 0.25

    while True:
        now = time.monotonic()
        remain = end - now
        if remain <= 0:
            bar = "#" * width
            sys.stdout.write(ANSI_RESET + f"\r{label:<10} [{bar}] 100% (0.0s)\n")
            sys.stdout.flush()
            return

        frac = (now - start) / (end - start) if end > start else 1.0
        frac = max(0.0, min(1.0, frac))
        filled = int(frac * width)
        bar = "#" * filled + "-" * (width - filled)

        do_invert = False
        if remain <= 1.0:
            if now >= next_toggle:
                invert = not invert
                next_toggle = now + flash_period
            do_invert = invert

        line = f"\r{label:<10} [{bar}] {int(frac*100):3d}% ({remain:4.1f}s) "
        sys.stdout.write((ANSI_REV if do_invert else ANSI_RESET) + line + ANSI_RESET)
        sys.stdout.flush()
        await asyncio.sleep(0.05)


def configure_resistance(mm: DMM6500, rng_text: str, nplc: float, autozero: str) -> None:
    rng = parse_range_text(rng_text)

    # Ensure resistance function
    mm.instrument.write("SENSe:FUNCtion 'RES'")

    if rng == "auto":
        mm.instrument.write("SENSe:RESistance:RANGe:AUTO ON")
    else:
        mm.instrument.write("SENSe:RESistance:RANGe:AUTO OFF")
        mm.instrument.write(f"SENSe:RESistance:RANGe {float(rng)}")

    mm.set_nplc(nplc)
    mm.set_autozero(autozero)


def capture_one(mm: DMM6500) -> float:
    return float(mm.measure_resistance(four_wire=False))


def capture_one_u1233a(mm: U1233A) -> float:
    value, _ = mm.get("MEAS")
    return float(value)


# ---------- Main loop ----------
async def run_async_dmm6500(address: str, rng_text: str, *, wait_s: float = 10.0, fmt: str = "{value:.12g}", nplc: float = 1.0, autozero: str = "off", no_close: bool = False):
    print(f"\nConnecting to instrument: {address}  |  range={rng_text}")

    mm = DMM6500(auto_connect=False)
    mm.connect(address=address)

    try:
        configure_resistance(mm, rng_text, nplc=nplc, autozero=autozero)

        print("\nReady.")
        print(f"- Press ENTER -> wait {wait_s:.0f}s -> capture ONE reading -> copy to clipboard.\n")

        try:
            while True:
                await wait_for_enter()

                ts = datetime.now().isoformat(timespec="seconds")
                print(f"\nArmed @ {ts}. Capturing in {wait_s:.0f}s…")
                await countdown(wait_s, label="Arming", flash_hz=4.0)

                try:
                    value = await asyncio.to_thread(capture_one, mm)
                except Exception as e:
                    print(f"✖ Measurement failed: {e}\n")
                    continue

                out = fmt.format(value=value)
                ok = copy_to_clipboard(out)

                if ok:
                    print(f"✔ {out}  (copied to clipboard)\n")
                else:
                    print(f"✔ {out}  (clipboard copy FAILED — printed above)\n")

        except KeyboardInterrupt:
            print("\nInterrupted by user.")
    finally:
        if not no_close:
            try:
                mm.disconnect()
            except Exception:
                pass


async def run_async_u1233a(com_port: str, *, wait_s: float = 10.0, fmt: str = "{value:.12g}", no_close: bool = False):
    print(f"\nConnecting to instrument: {com_port}  |  interface=pyserial")

    mm = U1233A(auto_connect=False)
    mm.connect(baud_rate=9600, com_port=com_port, prompt_on_fail=False)

    try:
        print("\nReady.")
        print(f"- Press ENTER -> wait {wait_s:.0f}s -> capture ONE reading -> copy to clipboard.\n")

        try:
            while True:
                await wait_for_enter()

                ts = datetime.now().isoformat(timespec="seconds")
                print(f"\nArmed @ {ts}. Capturing in {wait_s:.0f}s…")
                await countdown(wait_s, label="Arming", flash_hz=4.0)

                try:
                    value = await asyncio.to_thread(capture_one_u1233a, mm)
                except Exception as e:
                    print(f"✖ Measurement failed: {e}\n")
                    continue

                out = fmt.format(value=value)
                ok = copy_to_clipboard(out)

                if ok:
                    print(f"✔ {out}  (copied to clipboard)\n")
                else:
                    print(f"✔ {out}  (clipboard copy FAILED — printed above)\n")

        except KeyboardInterrupt:
            print("\nInterrupted by user.")
    finally:
        if not no_close:
            try:
                mm.disconnect()
            except Exception:
                pass


def main():
    print("Enter-triggered DMM capture (menu-driven)\n")

    interface = prompt_menu(
        "Select interface:",
        ["pyvisa (DMM6500)", "pyserial (U1233A)"]
    )

    # Other knobs (kept simple; edit defaults here if you want)
    wait_s = 10.0
    fmt = "{value:.12g}"
    nplc = 1.0
    autozero = "off"
    no_close = False

    if interface.startswith("pyvisa"):
        # Address menu
        resources = discover_visa_resources()
        if resources:
            address = prompt_menu("Select instrument address:", resources, allow_custom=True, custom_label="Enter manually…")
        else:
            print("No VISA resources auto-discovered (pyvisa not installed / no backend / none found).")
            address = input("Type the instrument address (e.g. USB0::...::INSTR): ").strip()
            if not address:
                print("Address required.")
                sys.exit(2)

        # Range menu
        range_options = [
            "auto",
            "10",
            "100",
            "1k",
            "10k",
            "100k",
            "1M",
            "10M",
        ]
        rng_text = prompt_menu("Select resistance range:", range_options, allow_custom=True, custom_label="Enter custom range…")

        asyncio.run(
            run_async_dmm6500(
                address,
                rng_text,
                wait_s=wait_s,
                fmt=fmt,
                nplc=nplc,
                autozero=autozero,
                no_close=no_close,
            )
        )
        return

    # pyserial path (U1233A)
    while True:
        ports = discover_serial_ports()
        if ports:
            port_items = [f"{dev} ({desc})" for dev, desc in ports]
            choice = prompt_menu("Select COM port:", port_items, allow_custom=True, custom_label="Enter manually…")
            if choice.endswith(")") and " (" in choice:
                com_port = choice.split(" (", 1)[0].strip()
            else:
                com_port = choice.strip()
        else:
            print("No COM ports auto-discovered (pyserial not installed / none found).")
            com_port = input("Type the COM port (e.g. COM3): ").strip()
            if not com_port:
                print("COM port required.")
                sys.exit(2)

        try:
            asyncio.run(
                run_async_u1233a(
                    com_port,
                    wait_s=wait_s,
                    fmt=fmt,
                    no_close=no_close,
                )
            )
            break
        except ConnectionError as exc:
            print(f"{exc}\n")


if __name__ == "__main__":
    main()
