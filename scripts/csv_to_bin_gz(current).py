#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv_to_current_bin_gz.py
Convert large Sample_Index,Value CSV to gzipped raw float32 binary + JSON metadata.

Binary layout (row-major): [Sample_Index, Value] for each row (2 columns)
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def convert(csv_path: Path, out_prefix: Path, sps: float, chunksize: int = 1_000_000, dtype: str = "float32") -> None:
    csv_path = Path(csv_path)
    out_prefix = Path(out_prefix)

    bin_path = out_prefix.with_suffix(".bin")
    gz_path = out_prefix.with_suffix(".bin.gz")
    meta_path = out_prefix.with_suffix(".json")

    # Read header for column names
    header = pd.read_csv(csv_path, nrows=0)
    colnames = list(header.columns)

    expected = ["Sample_Index", "Value"]
    if colnames != expected:
        # Still allow, but warn via exception message (keeps things strict & safe)
        raise ValueError(f"Expected columns {expected} exactly, got {colnames}")

    rows_written = 0
    cols = 2

    bin_path.parent.mkdir(parents=True, exist_ok=True)

    with open(bin_path, "wb") as f:
        for chunk in pd.read_csv(csv_path, chunksize=chunksize):
            # numeric + coercion
            chunk["Sample_Index"] = pd.to_numeric(chunk["Sample_Index"], errors="coerce")
            chunk["Value"] = pd.to_numeric(chunk["Value"], errors="coerce")

            arr = chunk.to_numpy(dtype=np.dtype(dtype), copy=False)
            arr[~np.isfinite(arr)] = np.nan

            arr.tofile(f)
            rows_written += arr.shape[0]

    # gzip compress
    with open(bin_path, "rb") as fin, gzip.open(gz_path, "wb", compresslevel=6) as fout:
        while True:
            block = fin.read(1024 * 1024)
            if not block:
                break
            fout.write(block)

    os.remove(bin_path)

    meta = {
        "source_csv": str(csv_path),
        "data_file": str(gz_path.name),
        "dtype": dtype,
        "rows": rows_written,
        "cols": cols,
        "colnames": colnames,
        "layout": "row_major",
        "sample_rate_sps": float(sps),
        "time_definition": "t = (Sample_Index - Sample_Index(1)) / sample_rate_sps",
        "units": {"Sample_Index": "count", "Value": "A"},
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote: {gz_path}")
    print(f"Wrote: {meta_path}")
    print(f"Rows: {rows_written}, Cols: {cols}, SPS: {sps}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, help="Input CSV path")
    ap.add_argument("--out", type=Path, default=Path("current_capture"), help="Output prefix (no extension)")
    ap.add_argument("--sps", type=float, default=500000.0, help="Sampling rate in samples per second")
    ap.add_argument("--chunksize", type=int, default=1_000_000, help="Rows per chunk")
    ap.add_argument("--dtype", type=str, default="float32", choices=["float32", "float64"], help="Binary dtype")
    args = ap.parse_args()

    convert(args.csv, args.out, args.sps, args.chunksize, args.dtype)


if __name__ == "__main__":
    main()
