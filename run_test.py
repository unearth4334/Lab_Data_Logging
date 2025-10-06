#!/usr/bin/env python3
# fetch_trace_and_plot.py
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

from data_logger import *  # your wrapper that returns mm = logger.connect("DMM6500")

def main():
    logger = data_logger()
    mm = logger.connect("DMM6500")
    try:
        # Download whatever is already in defbuffer1 (from your manual run)
        vals, times = mm.fetch_trace(buffer="defbuffer1", chunk=50000, debug=True, step=False)

        if not vals:
            print("No points in defbuffer1.")
            return

        # Choose x-axis
        if times and len(times) == len(vals):
            x = times
            xlabel = "Time (s, relative)"
        else:
            # Fallback: index axis
            x = list(range(len(vals)))
            xlabel = "Sample #"

        # Plot
        plt.figure(figsize=(10,6))
        plt.plot(x, vals, label="Trace")
        plt.title("DMM6500 Buffer Download (defbuffer1)")
        plt.xlabel(xlabel)
        plt.ylabel("Value (units of active function)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Optional: save CSV
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path("captures"); out.mkdir(exist_ok=True, parents=True)
        with (out / f"dmm6500_trace_{ts}.csv").open("w", encoding="utf-8") as f:
            if times and len(times) == len(vals):
                f.write("t,value\n")
                for t, v in zip(times, vals):
                    f.write(f"{t},{v}\n")
            else:
                f.write("index,value\n")
                for i, v in enumerate(vals):
                    f.write(f"{i},{v}\n")
        print(f"Saved {len(vals)} points -> {out / f'dmm6500_trace_{ts}.csv'}")

    finally:
        mm.disconnect()

if __name__ == "__main__":
    main()