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
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


MAX_FRAGMENT_BYTES = 50 * 1024 * 1024


def maybe_fragment_file(gz_path: Path, max_fragment_bytes: int = MAX_FRAGMENT_BYTES) -> dict | None:
    """Split large .bin.gz outputs into .bin.partNNN.gz files with a manifest."""
    size = gz_path.stat().st_size
    if size <= max_fragment_bytes:
        return None

    with open(gz_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    parts = []
    with open(gz_path, "rb") as src:
        idx = 0
        while True:
            block = src.read(max_fragment_bytes)
            if not block:
                break
            part_name = f"{gz_path.stem}.part{idx:03d}{gz_path.suffix}"
            part_path = gz_path.with_name(part_name)
            with open(part_path, "wb") as dst:
                dst.write(block)
            parts.append({
                "filename": part_name,
                "size": len(block),
                "index": idx,
            })
            idx += 1

    manifest_name = f"{gz_path.stem}.manifest.json"
    manifest_path = gz_path.with_name(manifest_name)
    manifest = {
        "original_filename": gz_path.name,
        "original_size": size,
        "original_hash": file_hash,
        "chunk_size": max_fragment_bytes,
        "chunk_count": len(parts),
        "chunks": parts,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    os.remove(gz_path)
    print(f"Fragmented: {manifest_path} ({len(parts)} chunks)")
    return manifest


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

    manifest = maybe_fragment_file(gz_path)

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
    if manifest:
        meta["fragmented"] = True
        meta["manifest_file"] = f"{gz_path.stem}.manifest.json"
        meta["chunk_count"] = manifest["chunk_count"]

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    if manifest:
        print(f"Wrote fragments for: {gz_path.name}")
    else:
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
