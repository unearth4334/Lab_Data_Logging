#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UV / OV Lockout Hysteresis Test (Package Version)
=================================================
"""

import time
import csv
from datetime import datetime
from pathlib import Path

from colorama import init as colorama_init, Fore, Style, Back

from .drivers import DMM6500, RigolDP711

colorama_init(autoreset=True)

# Default output directory (in user's current working directory)
DEFAULT_OUTPUT_DIR = Path.cwd() / "output" / "lockout_hysteresis"


# =============================================================================
# Console helpers
# =============================================================================

def hdr(text: str, color=Fore.CYAN):
    bar = "─" * 70
    print(f"\n{color}{bar}")
    print(f"{color}  {text}")
    print(f"{color}{bar}{Style.RESET_ALL}\n")


def status(text: str, color=Fore.WHITE):
    print(f"{color}  {text}{Style.RESET_ALL}")


def ok(text: str):
    print(f"{Fore.GREEN}  ✓ {text}{Style.RESET_ALL}")


def warn(text: str):
    print(f"{Fore.YELLOW}  ⚠ {text}{Style.RESET_ALL}")


def err(text: str):
    print(f"{Fore.RED}  ✗ {text}{Style.RESET_ALL}")


def debug_pause(msg: str, mode: str):
    """Pause / checkpoint between test phases."""
    if mode == "debug":
        try:
            input(f"\n{Back.YELLOW}{Fore.BLACK}  [DEBUG] {msg}  [press Enter] {Style.RESET_ALL}")
        except (EOFError, KeyboardInterrupt):
            print()
            raise KeyboardInterrupt
    elif mode == "auto":
        status(f"→ {msg}")
        time.sleep(1.0)
    else:
        status(f"→ {msg}")


# =============================================================================
# Sweep helpers
# =============================================================================

def build_sweep(v_start: float, v_end: float, v_step: float):
    """Return (sweep_up, sweep_down) as two lists of rounded float setpoints."""
    n_steps = round((v_end - v_start) / v_step)
    sweep_up   = [round(v_start + i * v_step, 6) for i in range(n_steps + 1)]
    sweep_down = [round(v_end   - i * v_step, 6) for i in range(1, n_steps + 1)]
    return sweep_up, sweep_down


# =============================================================================
# Data collection
# =============================================================================

def sweep_phase(ps, dmm, setpoints, label, settle_s, mode):
    """Step through setpoints, settling then reading DMM6500 at each point."""
    records = []
    n = len(setpoints)

    status(f"Starting {label} sweep – {n} points, settle={settle_s:.3f} s/step")

    for i, sp in enumerate(setpoints, start=1):
        ps.set_voltage(sp)
        time.sleep(settle_s)

        try:
            dmm_v = dmm.measure_voltage()
        except Exception as exc:
            warn(f"  DMM read error at {sp:.4f} V: {exc}")
            dmm_v = float("nan")

        try:
            ps_v = ps.measure_voltage()
        except Exception as exc:
            warn(f"  PS readback error at {sp:.4f} V: {exc}")
            ps_v = float("nan")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]
        records.append({
            "setpoint_v": sp,
            "dmm_v":      dmm_v,
            "ps_v":       ps_v,
            "phase":      label,
            "timestamp":  ts,
        })

        if i == 1 or i == n or i % 50 == 0:
            status(f"  [{label}] {i:4d}/{n}  SP={sp:.4f} V  DMM={dmm_v:.6f} V  PS={ps_v:.6f} V")

    ok(f"{label} sweep complete – {n} readings")
    return records


# =============================================================================
# Save CSV
# =============================================================================

def save_csv(records, output_dir):
    """Save records to CSV file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"lockout_hysteresis_{ts}.csv"

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["# UV/OV Lockout Hysteresis Test"])
        writer.writerow([f"# Date: {ts}"])
        writer.writerow([])
        writer.writerow(["Phase", "Setpoint (V)", "DP711 Meas (V)", "DMM6500 Meas (V)", "Timestamp"])
        for r in records:
            writer.writerow([
                r["phase"],
                f"{r['setpoint_v']:.4f}",
                f"{r['ps_v']:.6f}",
                f"{r['dmm_v']:.6f}",
                r["timestamp"],
            ])

    ok(f"CSV saved: {path}")
    return path


# =============================================================================
# Plot
# =============================================================================

def plot_results(records, csv_path, v_start, v_end):
    """Plot DMM6500 measured voltage vs DP711 setpoint."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        warn("plotly not installed – skipping plot (pip install plotly)")
        return

    up_sp   = [r["setpoint_v"] for r in records if r["phase"] == "UP"]
    up_dmm  = [r["dmm_v"]      for r in records if r["phase"] == "UP"]
    dn_sp   = [r["setpoint_v"] for r in records if r["phase"] == "DOWN"]
    dn_dmm  = [r["dmm_v"]      for r in records if r["phase"] == "DOWN"]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=up_sp, y=up_dmm,
        mode="lines",
        name="Sweep ↑ (rising)",
        line=dict(color="#e05c1a", width=1.5),
    ))

    fig.add_trace(go.Scatter(
        x=dn_sp, y=dn_dmm,
        mode="lines",
        name="Sweep ↓ (falling)",
        line=dict(color="#1a6fe0", width=1.5),
    ))

    fig.add_trace(go.Scatter(
        x=[v_start, v_end],
        y=[v_start, v_end],
        mode="lines",
        name="Ideal (DMM = setpoint)",
        line=dict(color="#aaaaaa", width=1, dash="dot"),
    ))

    # Detect hysteresis band
    up_dict = dict(zip(up_sp,  up_dmm))
    dn_dict = dict(zip(dn_sp,  dn_dmm))
    common  = sorted(set(up_dict) & set(dn_dict))
    max_diff = 0.0
    max_sp   = None
    for sp in common:
        diff = abs(up_dict[sp] - dn_dict[sp])
        if diff > max_diff:
            max_diff = diff
            max_sp   = sp

    if max_sp is not None and max_diff > 0.001:
        fig.add_annotation(
            x=max_sp,
            y=max(up_dict[max_sp], dn_dict[max_sp]),
            text=(f"Max hysteresis<br>"
                  f"SP={max_sp:.3f} V<br>"
                  f"ΔV={max_diff*1000:.1f} mV"),
            showarrow=True,
            arrowhead=2,
            ax=60, ay=-40,
            font=dict(color="#9b59b6", size=12),
            arrowcolor="#9b59b6",
            bgcolor="white",
            bordercolor="#9b59b6",
            borderwidth=1,
        )

    fig.update_layout(
        title="UV / OV Lockout Hysteresis – DMM6500 vs DP711 Voltage Setpoint",
        xaxis_title="DP711 Setpoint (V)",
        yaxis_title="DMM6500 Measured Voltage (V)",
        template="plotly_white",
        height=500,
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
    )

    html_path = csv_path.with_suffix(".html")
    fig.write_html(str(html_path))
    fig.show()
    ok(f"Plot saved: {html_path}")


# =============================================================================
# Main API
# =============================================================================

def run_lockout_test(v_start=10.0, v_end=14.0, v_step=0.005,
                     settle_s=0.05, current_limit_a=2.0,
                     mode="debug", com_port=None,
                     output_dir=None):
    """
    Run the complete lockout hysteresis test.
    
    Args:
        v_start: Start voltage (V)
        v_end: End voltage (V)
        v_step: Step size (V)
        settle_s: Settling delay per step (seconds)
        current_limit_a: DP711 current limit (A)
        mode: 'debug', 'auto', or 'off'
        com_port: COM port for DP711 (or None to auto-select)
        output_dir: Output directory (or None for default)
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    else:
        output_dir = Path(output_dir)

    hdr("UV / OV LOCKOUT HYSTERESIS TEST – STARTING", color=Fore.MAGENTA)
    status(f"Sweep: {v_start:.3f} V → {v_end:.3f} V → {v_start:.3f} V "
           f"in {v_step*1000:.1f} mV steps")
    status(f"Current limit: {current_limit_a:.2f} A   |   Settle: {settle_s*1000:.0f} ms/step")
    status(f"Run mode: {mode}")
    status(f"Output directory: {output_dir.resolve()}")

    sweep_up, sweep_down = build_sweep(v_start, v_end, v_step)
    total_points = len(sweep_up) + len(sweep_down)
    status(f"Total setpoints: {total_points}  "
           f"({len(sweep_up)} rising + {len(sweep_down)} falling)")

    # Connect instruments
    hdr("INSTRUMENT SETUP", color=Fore.CYAN)
    
    status("Connecting to DMM6500…")
    dmm = DMM6500()
    ok(f"DMM6500 connected: {dmm.status}")

    status("Connecting to DP711…")
    ps = RigolDP711(com_port=com_port)
    ok(f"DP711 connected: {ps.identity}  @  {ps.address}")

    # Instrument setup
    debug_pause(f"About to set DP711 to {v_start:.3f} V / {current_limit_a:.2f} A and enable output.", mode)

    status(f"Setting DP711: {v_start:.3f} V, {current_limit_a:.2f} A limit…")
    ps.set_voltage(v_start)
    ps.set_current(current_limit_a)
    ps.turn_on()
    ok(f"DP711 ON: {v_start:.3f} V")

    status("Waiting 1 s for DUT to stabilise…")
    time.sleep(1.0)

    try:
        v_init = dmm.measure_voltage()
        ok(f"DMM6500 initial reading: {v_init:.6f} V")
    except Exception as exc:
        warn(f"DMM6500 initial read failed: {exc}")

    # Rising sweep
    debug_pause(f"Starting RISING sweep: {v_start:.3f} V → {v_end:.3f} V "
                f"({len(sweep_up)} steps)", mode)

    records_up = sweep_phase(ps, dmm, sweep_up, "UP", settle_s, mode)

    # Falling sweep
    debug_pause(f"Starting FALLING sweep: {v_end:.3f} V → {v_start:.3f} V "
                f"({len(sweep_down)} steps)", mode)

    records_dn = sweep_phase(ps, dmm, sweep_down, "DOWN", settle_s, mode)

    # Power down
    debug_pause("Sweep complete. About to return DP711 to start voltage and disable output.", mode)

    status(f"Returning DP711 to {v_start:.3f} V…")
    ps.set_voltage(v_start)
    time.sleep(0.5)
    ps.turn_off()
    ok("DP711 OFF")

    # Save and plot
    all_records = records_up + records_dn
    hdr("SAVING RESULTS", color=Fore.CYAN)

    csv_path = save_csv(all_records, output_dir)

    # Summary statistics
    import math
    up_dmm  = [r["dmm_v"] for r in records_up  if not math.isnan(r["dmm_v"])]
    dn_dmm  = [r["dmm_v"] for r in records_dn  if not math.isnan(r["dmm_v"])]

    hdr("TEST COMPLETE – SUMMARY", color=Fore.GREEN)
    print(f"  {'Phase':<12}  {'Points':<8}  {'DMM min (V)':<14}  {'DMM max (V)':<14}")
    print(f"  {'─'*12}  {'─'*8}  {'─'*14}  {'─'*14}")
    if up_dmm:
        print(f"  {'Rising':<12}  {len(up_dmm):<8}  {min(up_dmm):<14.6f}  {max(up_dmm):<14.6f}")
    if dn_dmm:
        print(f"  {'Falling':<12}  {len(dn_dmm):<8}  {min(dn_dmm):<14.6f}  {max(dn_dmm):<14.6f}")
    print()

    debug_pause("About to display the hysteresis plot.", mode)
    plot_results(all_records, csv_path, v_start, v_end)

    # Cleanup
    dmm.disconnect()
    ps.disconnect()
