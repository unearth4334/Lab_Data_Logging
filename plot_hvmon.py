import time
import math
import httpx
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional

from libs.KeysightMSOX4154A import KeysightMSOX4154A

BASE_URL = "http://127.0.0.1:7860"   # FastAPI backend for the GEN4 power GUI
DWELL_SEC = 2.0                      # dwell time after setting wavegen voltage
V_START = 0.0
V_STOP  = -3.3
V_STEP  = -0.01
SAMPLES_PER_POINT = 3                # average N readings per dwell
SAMPLE_INTERVAL   = 0.2              # gap between readings when averaging


def frange(start: float, stop: float, step: float) -> List[float]:
    """Inclusive floating range handling negative steps safely."""
    vals = []
    v = start
    if step == 0:
        raise ValueError("step cannot be zero")
    if step > 0:
        while v <= stop + 1e-9:
            vals.append(round(v, 4))
            v += step
    else:
        while v >= stop - 1e-9:
            vals.append(round(v, 4))
            v += step
    if abs(vals[-1] - stop) > 1e-9:
        vals.append(round(stop, 4))
    return vals


def read_hv(client: httpx.Client) -> Tuple[Optional[float], Optional[float]]:
    """Read HV_MON_L and HV_MON_R once from /state."""
    r = client.get(f"{BASE_URL}/state", timeout=5.0)
    r.raise_for_status()
    data = r.json()
    md = data.get("monitor_data", {}) or {}
    hv_l = md.get("hv_mon_l_voltage")
    hv_r = md.get("hv_mon_r_voltage")
    try:
        hv_l = float(hv_l) if hv_l is not None else None
    except Exception:
        hv_l = None
    try:
        hv_r = float(hv_r) if hv_r is not None else None
    except Exception:
        hv_r = None
    return hv_l, hv_r


def read_hv_avg(client: httpx.Client, samples: int, interval: float) -> Tuple[Optional[float], Optional[float]]:
    """Average N readings with delay between them; ignore None values in mean."""
    l_vals: List[float] = []
    r_vals: List[float] = []
    for i in range(max(1, samples)):
        hv_l, hv_r = read_hv(client)
        if hv_l is not None and math.isfinite(hv_l):
            l_vals.append(hv_l)
        if hv_r is not None and math.isfinite(hv_r):
            r_vals.append(hv_r)
        if i < samples - 1:
            time.sleep(interval)
    l_mean = sum(l_vals) / len(l_vals) if l_vals else None
    r_mean = sum(r_vals) / len(r_vals) if r_vals else None
    return l_mean, r_mean


def main():
    sweep_volts = frange(V_START, V_STOP, V_STEP)
    osc = KeysightMSOX4154A()
    client = httpx.Client(timeout=5.0)

    hv_l_results: List[Optional[float]] = []
    hv_r_results: List[Optional[float]] = []

    try:
        print("Starting sweep:")
        for v in sweep_volts:
            osc.set_wgen1_offset(v)
            osc.set_wgen2_offset(v)
            print(f"  Set WGEN1 & WGEN2 offset -> {v:+.3f} V; dwell {DWELL_SEC:.1f}s ...", end="", flush=True)
            time.sleep(DWELL_SEC)

            hv_l, hv_r = read_hv_avg(client, SAMPLES_PER_POINT, SAMPLE_INTERVAL)
            hv_l_results.append(hv_l)
            hv_r_results.append(hv_r)
            print(f"  HV_MON_L={hv_l if hv_l is not None else 'None'} V, HV_MON_R={hv_r if hv_r is not None else 'None'} V")

        # --- Save combined CSV ---
        with open("hv_sweep_results.csv", "w", newline="") as f:
            f.write("wavegen_v,hv_mon_l_v,hv_mon_r_v\n")
            for v, l, r in zip(sweep_volts, hv_l_results, hv_r_results):
                l_str = "" if l is None else f"{l:.6f}"
                r_str = "" if r is None else f"{r:.6f}"
                f.write(f"{v:.6f},{l_str},{r_str}\n")
        print("Saved combined CSV -> hv_sweep_results.csv")

        # --- Save raw separate CSVs ---
        with open("hv_mon_l_raw.csv", "w", newline="") as f:
            f.write("wavegen_v,hv_mon_l_v\n")
            for v, l in zip(sweep_volts, hv_l_results):
                l_str = "" if l is None else f"{l:.6f}"
                f.write(f"{v:.6f},{l_str}\n")
        print("Saved HV_MON_L raw CSV -> hv_mon_l_raw.csv")

        with open("hv_mon_r_raw.csv", "w", newline="") as f:
            f.write("wavegen_v,hv_mon_r_v\n")
            for v, r in zip(sweep_volts, hv_r_results):
                r_str = "" if r is None else f"{r:.6f}"
                f.write(f"{v:.6f},{r_str}\n")
        print("Saved HV_MON_R raw CSV -> hv_mon_r_raw.csv")

        # --- Plot HV_MON_L ---
        plt.figure()
        plt.title("HV_MON_L vs Wavegen Offset")
        plt.xlabel("Wavegen Offset (V)")
        plt.ylabel("HV_MON_L (V)")
        x_l = [v for v, y in zip(sweep_volts, hv_l_results) if y is not None]
        y_l = [y for y in hv_l_results if y is not None]
        plt.plot(x_l, y_l, marker="o")
        plt.grid(True)
        plt.savefig("hv_mon_l_vs_wavegen.png", dpi=150, bbox_inches="tight")
        print("Saved HV_MON_L plot -> hv_mon_l_vs_wavegen.png")

        # --- Plot HV_MON_R ---
        plt.figure()
        plt.title("HV_MON_R vs Wavegen Offset")
        plt.xlabel("Wavegen Offset (V)")
        plt.ylabel("HV_MON_R (V)")
        x_r = [v for v, y in zip(sweep_volts, hv_r_results) if y is not None]
        y_r = [y for y in hv_r_results if y is not None]
        plt.plot(x_r, y_r, marker="o")
        plt.grid(True)
        plt.savefig("hv_mon_r_vs_wavegen.png", dpi=150, bbox_inches="tight")
        print("Saved HV_MON_R plot -> hv_mon_r_vs_wavegen.png")

        try:
            plt.show()
        except Exception:
            pass

    finally:
        try:
            osc.disconnect()
        except Exception:
            pass
        client.close()


if __name__ == "__main__":
    main()