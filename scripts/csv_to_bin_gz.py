#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv_to_bin_gz.py
Convert large CSV (numeric columns) to compressed raw binary for MATLAB.

Output:
  - <out_prefix>.bin.gz   : gzipped raw float32 stream, row-major
  - <out_prefix>.json     : metadata (column names, dtype, rows, cols)
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def convert_csv_to_bin_gz(
    csv_path: Path,
    out_prefix: Path,
    chunksize: int = 500_000,
    dtype: str = "float32",
) -> None:
    csv_path = Path(csv_path)
    out_prefix = Path(out_prefix)

    bin_path = out_prefix.with_suffix(".bin")
    gz_path = out_prefix.with_suffix(".bin.gz")
    meta_path = out_prefix.with_suffix(".json")

    # First pass: grab header/columns only
    # NOTE: keep_default_na=False helps avoid weird NA parsing for large files
    header_df = pd.read_csv(csv_path, nrows=0)
    colnames = list(header_df.columns)
    if len(colnames) < 2:
        raise ValueError("Expected at least 2 columns (time + signals).")

    # Stream write raw binary (uncompressed), then gzip it in one pass at end.
    rows_written = 0
    cols = len(colnames)

    # Ensure parent dir exists
    bin_path.parent.mkdir(parents=True, exist_ok=True)

    # Chunked load/write
    with open(bin_path, "wb") as f:
        for chunk in pd.read_csv(csv_path, chunksize=chunksize):
            # Force numeric conversion (coerce errors to NaN)
            # If your CSV is clean numeric already, this is still safe.
            for c in colnames:
                chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

            arr = chunk.to_numpy(dtype=np.dtype(dtype), copy=False)

            # Optional: replace NaN/inf with sentinel or zeros
            # Here we keep NaN but also squash inf to NaN to avoid MATLAB surprises.
            arr[~np.isfinite(arr)] = np.nan

            arr.tofile(f)
            rows_written += arr.shape[0]

    # Gzip compress the raw binary file
    # (This keeps MATLAB side simple: gunzip + fread)
    with open(bin_path, "rb") as fin, gzip.open(gz_path, "wb", compresslevel=6) as fout:
        while True:
            block = fin.read(1024 * 1024)
            if not block:
                break
            fout.write(block)

    # Remove the uncompressed .bin to save space
    os.remove(bin_path)

    meta = {
        "source_csv": str(csv_path),
        "data_file": str(gz_path.name),
        "dtype": dtype,
        "rows": rows_written,
        "cols": cols,
        "colnames": colnames,  # first one should be "Time [s]"
        "layout": "row_major",
        "description": "Gzipped raw binary stream. Read as dtype, reshape to [cols, rows], then transpose to [rows, cols].",
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote: {gz_path}")
    print(f"Wrote: {meta_path}")
    print(f"Rows: {rows_written}, Cols: {cols}, DType: {dtype}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, help="Input CSV path")
    ap.add_argument("--out", type=Path, default=Path("power_rails"), help="Output prefix (no extension)")
    ap.add_argument("--chunksize", type=int, default=500_000, help="Rows per chunk")
    ap.add_argument("--dtype", type=str, default="float32", choices=["float32", "float64"], help="Binary dtype")
    args = ap.parse_args()

    convert_csv_to_bin_gz(args.csv, args.out, args.chunksize, args.dtype)


if __name__ == "__main__":
    main()
