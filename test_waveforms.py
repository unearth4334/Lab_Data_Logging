#!/usr/bin/env python3
# test_waveforms.py

from __future__ import annotations

import sys, os, csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import matplotlib.pyplot as plt

import matplotlib.widgets as mwidgets

from libs.KeysightMSOX4154A import KeysightMSOX4154A
from data_logger import data_logger  # Your DMM6500 logger

# ===== Sampling rates =====
DMM6500_SAMPLING_RATE_HZ = 1_000_000.0  # 1 MS/s (used if the logger doesn't return timestamps)

def save_csv(path: Path, t: List[float], y: List[float], header=("t (s)", "V (V)")) -> None:
    """Save time + signal data to CSV."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(zip(t, y))

def main():
    # ---- args: outdir + one or more VISA addresses ----
    if len(sys.argv) < 3:
        print("Usage: python test_waveforms.py <outdir> <VISA1> <VISA2> [<VISA3> ...]")
        print('Example: python test_waveforms.py ./captures "USB0::0x0957::0x17BC::MY59241237::INSTR" "USB0::0x0957::0x17BC::MY56310625::INSTR"')
        sys.exit(2)

    outdir = Path(sys.argv[1])
    addrs = sys.argv[2:]
    outdir.mkdir(parents=True, exist_ok=True)
    os.chdir(outdir)
    print(f"Output directory: {Path.cwd()}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_waveforms: List[Tuple[str, List[float], List[float]]] = []

    try:
        # --- Oscilloscopes: get true timebase + volts ---
        for idx, addr in enumerate(addrs, 1):
            osc = KeysightMSOX4154A(auto_connect=False)
            osc.connect(addr)
            idn = osc.get_idn()
            print(f"Opened: {addr}  [{idn}]")
            serial = idn.split(',')[2] if ',' in idn else f"OSC{idx}"

            # Capture CH1..CH4
            for ch in range(1, 5):
                source = f"CHAN{ch}"
                # get_waveform returns (t_seconds, volts, meta) using scope preamble (XINCR, etc.)
                t, y, meta = osc.get_waveform(
                    source=source,
                    points_mode="RAW",
                    points=None,
                    stop_during_read=True,
                    debug=True
                )

                csv_name = f"waveform_OSC{idx}_{serial}_{source}_{ts}.csv"
                save_csv(Path(csv_name), t, y, header=("t (s)", "V (V)"))
                fs = meta.get("sample_rate_hz", None)
                fs_str = f"{fs:.6g} Hz" if isinstance(fs, (int, float)) else "?"
                print(f"Saved CSV -> {csv_name}  ({len(y)} pts, Fs ≈ {fs_str})")
                all_waveforms.append((f"OSC{idx} {source}", t, y))

            osc.disconnect()

        # --- DMM6500 current trace ---
        logger = data_logger()
        mm = logger.connect("DMM6500")
        vals, times = mm.fetch_trace(buffer="defbuffer1", chunk=50000, debug=True, step=False)
        mm.disconnect()

        if not vals:
            print("No points in DMM6500 defbuffer1.")
            dmm_trace = None
        else:
            # Prefer device-provided timestamps if available and aligned
            if times and len(times) == len(vals):
                dmm_t = times
                time_header = "t (s)"
                print("DMM6500: using device-provided timestamps.")
            else:
                # Build time axis using fixed sampling rate (70 kS/s)
                dt = 1.0 / DMM6500_SAMPLING_RATE_HZ
                dmm_t = [i * dt for i in range(len(vals))]
                time_header = "t (s)"
                print(f"DMM6500: timestamps not provided; using fixed Fs = {DMM6500_SAMPLING_RATE_HZ:g} Hz.")

            dmm_csv = f"dmm6500_trace_{ts}.csv"
            save_csv(Path(dmm_csv), dmm_t, vals, header=(time_header, "Current (A)"))
            print(f"Saved DMM6500 CSV -> {dmm_csv}  ({len(vals)} pts)")
            dmm_trace = (dmm_t, vals, "Time (s)")


            plt.figure(figsize=(14, 7))
            ax1 = plt.gca()
            lines = []
            trace_labels = []
            for label, tvec, yvec in all_waveforms:
                line, = ax1.plot(tvec, yvec, label=label, picker=5)
                lines.append(line)
                trace_labels.append(label)
            ax1.set_title("MSOX4154A All Channels (OSC1 & OSC2) + DMM6500 Current")
            ax1.set_xlabel("Time (s)")
            ax1.set_ylabel("Voltage (V)")
            ax1.grid(True)

            # Plot DMM6500 current on right y-axis (time or index depending on source)
            dmm_line = None
            if dmm_trace:
                ax2 = ax1.twinx()
                dmm_x, dmm_y, _ = dmm_trace
                dmm_line, = ax2.plot(dmm_x, dmm_y, color="k", label="DMM6500 Current", linewidth=2, alpha=0.7)
                ax2.set_ylabel("Current (A)")
                ax2.legend(loc="upper right")
                lines.append(dmm_line)
                trace_labels.append("DMM6500 Current")

            ax1.legend(loc="upper left")
            plt.tight_layout()
            plot_name = f"waveforms_all_OSC1_OSC2_DMM6500_{ts}.png"
            plt.savefig(plot_name, dpi=120)
            print(f"Saved plot -> {plot_name}")

            # --- RadioButtons for trace selection (Dropdown not available in matplotlib.widgets) ---
            # Add "None" as the first option
            radio_labels = ["None"] + trace_labels
            ax_radio = plt.axes([0.15, 0.88, 0.2, 0.12])  # Increased height for more options
            radio = mwidgets.RadioButtons(ax_radio, radio_labels)

            # --- Cursor and annotation ---
            mwidgets.Cursor(ax1, useblit=True, color='red', linewidth=1)  # Cursor created for interactivity
            annot = ax1.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                 bbox=dict(boxstyle="round", fc="w"),
                 arrowprops=dict(arrowstyle="->"))
            annot.set_visible(False)

            # Helper to get data from selected line
            def get_line_data(idx):
                line = lines[idx]
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                return xdata, ydata

            selected_idx = [None]  # None means no trace selected

            def on_radio_change(label):
                if label == "None":
                    selected_idx[0] = None
                    for line in lines:
                        line.set_linewidth(1)
                        line.set_alpha(1.0)  # Show all traces normally
                    annot.set_visible(False)
                else:
                    idx = trace_labels.index(label)
                    selected_idx[0] = idx
                    for i, line in enumerate(lines):
                        line.set_linewidth(2 if i == idx else 1)
                        line.set_alpha(1.0 if i == idx else 0.3)
                    annot.set_visible(False)
                plt.draw()

            radio.on_clicked(on_radio_change)
            on_radio_change("None")  # highlight initial (None)

            def on_mouse_move(event):
                if not event.inaxes or selected_idx[0] is None:
                    annot.set_visible(False)
                    plt.draw()
                    return
                idx = selected_idx[0]
                xdata, ydata = get_line_data(idx)
                if len(xdata) == 0:
                    annot.set_visible(False)
                    plt.draw()
                    return
                # Find nearest data point
                x = event.xdata
                ind = min(range(len(xdata)), key=lambda i: abs(xdata[i] - x))
                x_near, y_near = xdata[ind], ydata[ind]
                annot.xy = (x_near, y_near)
                annot.set_text(f"x={x_near:.6g}\ny={y_near:.6g}")
                annot.set_visible(True)
                plt.draw()

            plt.gcf().canvas.mpl_connect("motion_notify_event", on_mouse_move)

            plt.show()

    finally:
        pass  # Instruments are disconnected above

if __name__ == "__main__":
    main()