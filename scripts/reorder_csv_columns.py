#!/usr/bin/env python3
"""
reorder_csv_columns.py

Interactive tool for large CSVs:
  1) Lists headers with indexes
  2) Optionally renames headers (by index) in a loop
  3) Prompts for a comma-delimited list of indexes in the desired order
  4) Shows the proposed new header order for approval
  5) Streams input -> output with reordered columns (handles big files)

Usage:
  python reorder_csv_columns.py input.csv -o output.csv
  python reorder_csv_columns.py input.csv --inplace   # writes input.csv.tmp then replaces input.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from typing import List, Tuple


def sniff_dialect(path: str, sample_bytes: int = 1_000_000) -> csv.Dialect:
    """Best-effort dialect sniff (delimiter, quoting). Falls back to excel."""
    with open(path, "r", newline="", encoding="utf-8", errors="replace") as f:
        sample = f.read(sample_bytes)
    try:
        return csv.Sniffer().sniff(sample)
    except Exception:
        return csv.excel


def read_header(path: str, dialect: csv.Dialect) -> List[str]:
    with open(path, "r", newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f, dialect)
        header = next(r, None)
    if header is None:
        raise RuntimeError("CSV appears empty (no header row).")
    return header


def print_header_with_indexes(header: List[str]) -> None:
    print("\n=== Columns (index: name) ===")
    for i, name in enumerate(header):
        print(f"{i:4d}: {name}")
    print(f"Total columns: {len(header)}\n")


def prompt_int(prompt: str, lo: int | None = None, hi: int | None = None) -> int:
    while True:
        s = input(prompt).strip()
        try:
            v = int(s)
        except ValueError:
            print("Please enter an integer.")
            continue
        if lo is not None and v < lo:
            print(f"Must be >= {lo}.")
            continue
        if hi is not None and v > hi:
            print(f"Must be <= {hi}.")
            continue
        return v


def prompt_yes_no(prompt: str, default: bool | None = None) -> bool:
    suffix = " [y/n] "
    if default is True:
        suffix = " [Y/n] "
    elif default is False:
        suffix = " [y/N] "
    while True:
        s = input(prompt + suffix).strip().lower()
        if not s and default is not None:
            return default
        if s in ("y", "yes"):
            return True
        if s in ("n", "no"):
            return False
        print("Please enter y or n.")


def rename_loop(header: List[str]) -> List[str]:
    """Interactive rename loop by index."""
    while True:
        print_header_with_indexes(header)
        idx = prompt_int("Rename a column: enter index to rename, or -1 to continue: ", lo=-1, hi=len(header)-1)
        if idx == -1:
            return header
        old = header[idx]
        new = input(f"New name for [{idx}] '{old}': ").strip()
        if not new:
            print("Name cannot be empty. No change made.")
            continue
        header[idx] = new
        print(f"Renamed [{idx}] '{old}' -> '{new}'")


def parse_index_list(s: str, ncols: int) -> List[int]:
    raw = [p.strip() for p in s.split(",") if p.strip() != ""]
    if not raw:
        raise ValueError("No indexes provided.")
    idxs: List[int] = []
    for p in raw:
        if not p.lstrip("-").isdigit():
            raise ValueError(f"Not an integer index: '{p}'")
        v = int(p)
        if v < 0 or v >= ncols:
            raise ValueError(f"Index out of range: {v} (valid 0..{ncols-1})")
        idxs.append(v)

    # Must be a permutation: include each index exactly once
    if len(idxs) != ncols:
        raise ValueError(f"You provided {len(idxs)} indexes but there are {ncols} columns.")
    if len(set(idxs)) != ncols:
        raise ValueError("Duplicate index detected. Provide each index exactly once.")
    return idxs


def propose_new_order(header: List[str], order: List[int]) -> List[str]:
    return [header[i] for i in order]


def reorder_streaming(
    in_path: str,
    out_path: str,
    dialect: csv.Dialect,
    order: List[int],
    header_out: List[str],
) -> Tuple[int, int]:
    """
    Stream rows without loading entire file:
      - Reads input header row and discards it
      - Writes new header_out
      - Reorders each row by 'order'
    Returns: (rows_written, bad_rows)
    """
    rows_written = 0
    bad_rows = 0

    with open(in_path, "r", newline="", encoding="utf-8", errors="replace") as fin, \
         open(out_path, "w", newline="", encoding="utf-8") as fout:

        reader = csv.reader(fin, dialect)
        writer = csv.writer(fout, dialect)

        in_header = next(reader, None)
        if in_header is None:
            raise RuntimeError("CSV appears empty (no header row).")

        writer.writerow(header_out)

        ncols = len(in_header)
        for row in reader:
            if len(row) != ncols:
                bad_rows += 1
                # Pad/truncate to avoid crashing, but record as bad.
                if len(row) < ncols:
                    row = row + [""] * (ncols - len(row))
                else:
                    row = row[:ncols]
            writer.writerow([row[i] for i in order])
            rows_written += 1

    return rows_written, bad_rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Interactively rename and reorder CSV columns (streaming for large files).")
    ap.add_argument("input_csv", help="Input CSV file path")
    ap.add_argument("-o", "--output", help="Output CSV path (default: <input>.reordered.csv)")
    ap.add_argument("--inplace", action="store_true", help="Replace input file (writes temp then moves into place)")
    ap.add_argument("--no-sniff", action="store_true", help="Don't sniff dialect; use csv.excel defaults")
    args = ap.parse_args()

    in_path = args.input_csv
    if not os.path.isfile(in_path):
        print(f"Input file not found: {in_path}", file=sys.stderr)
        return 2

    if args.inplace and args.output:
        print("Choose either --inplace or --output, not both.", file=sys.stderr)
        return 2

    dialect = csv.excel if args.no_sniff else sniff_dialect(in_path)
    header = read_header(in_path, dialect)

    print_header_with_indexes(header)

    # 1) Rename loop
    if prompt_yes_no("Do you want to rename any columns?", default=False):
        header = rename_loop(header)

    # 2) Order prompt
    ncols = len(header)
    print("\nEnter the NEW column order as a comma-delimited list of indexes.")
    print(f"It must contain each index 0..{ncols-1} exactly once.")
    while True:
        s = input("New order indexes: ").strip()
        try:
            order = parse_index_list(s, ncols)
            break
        except Exception as e:
            print(f"Invalid order: {e}")

    new_header = propose_new_order(header, order)

    print("\n=== Proposed new header order ===")
    for i, name in enumerate(new_header):
        print(f"{i:4d}: {name}")
    print()

    if not prompt_yes_no("Approve and write the reordered CSV?", default=True):
        print("Aborted. No files written.")
        return 0

    # Output path selection
    if args.inplace:
        out_path = in_path + ".tmp_reordered"
        final_path = in_path
    else:
        out_path = args.output or (in_path + ".reordered.csv")
        final_path = out_path

    print(f"\nWriting output to: {final_path}")
    rows_written, bad_rows = reorder_streaming(
        in_path=in_path,
        out_path=out_path,
        dialect=dialect,
        order=order,
        header_out=new_header,
    )

    if args.inplace:
        # Backup original to .bak (safe move) then replace
        bak_path = in_path + ".bak"
        print(f"Creating backup: {bak_path}")
        shutil.copy2(in_path, bak_path)
        shutil.move(out_path, in_path)

    print(f"Done. Rows written: {rows_written}.")
    if bad_rows:
        print(f"Warning: {bad_rows} rows had an unexpected column count and were padded/truncated.")

    return 0


if __name__ == "__main__":
    main()
