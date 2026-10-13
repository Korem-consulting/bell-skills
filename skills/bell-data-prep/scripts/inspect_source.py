#!/usr/bin/env python3
"""Inspect a data file without printing its contents.

    python inspect_source.py FILE [--sheet NAME] [--sample 20] [--sep ,]

Prints shape, per-column dtype / nulls / distinct count, a bounded sample of
rows, and a profile of the columns that look like dates or markets. The
sample size is capped at 50 no matter what is asked for: this script exists
so an agent never has to open a client's file, and a cap it can raise is no
cap at all.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HARD_SAMPLE_CAP = 50
TOP_VALUES = 10


def read_any(path: str, sheet: str | None = None, sep: str | None = None, **kw) -> pd.DataFrame:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, sheet_name=sheet or 0, **kw)
    if ext in (".parquet", ".pq"):
        return pd.read_parquet(p)
    if ext in (".json", ".jsonl", ".ndjson"):
        return pd.read_json(p, lines=ext != ".json")
    # csv / tsv / txt: sniff the separator unless given
    return pd.read_csv(p, sep=sep if sep else None, engine="python", **kw)


def _looks_like_date(s: pd.Series) -> tuple[float, pd.Timestamp | None, pd.Timestamp | None]:
    if pd.api.types.is_datetime64_any_dtype(s):
        d = s.dropna()
        return 1.0, d.min(), d.max()
    if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
        return 0.0, None, None
    parsed = pd.to_datetime(s, errors="coerce", format="mixed")
    rate = float(parsed.notna().mean()) if len(parsed) else 0.0
    d = parsed.dropna()
    return rate, (d.min() if len(d) else None), (d.max() if len(d) else None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--sep", default=None)
    ap.add_argument("--skiprows", type=int, default=0)
    args = ap.parse_args()

    n_sample = max(0, min(args.sample, HARD_SAMPLE_CAP))
    df = read_any(args.file, sheet=args.sheet, sep=args.sep, skiprows=args.skiprows)

    print(f"file: {args.file}")
    print(f"shape: {df.shape[0]:,} rows x {df.shape[1]} columns\n")

    print("columns:")
    for c in df.columns:
        s = df[c]
        print(f"  {str(c)!r:40} {str(s.dtype):14} nulls={int(s.isna().sum()):>9,}  distinct={int(s.nunique(dropna=True)):>9,}")

    print(f"\nsample ({n_sample} rows, head):")
    with pd.option_context("display.max_columns", 30, "display.width", 200, "display.max_colwidth", 32):
        print(df.head(n_sample).to_string(index=False) if n_sample else "  (suppressed)")

    print("\ncolumn profiles:")
    for c in df.columns:
        s = df[c]
        rate, lo, hi = _looks_like_date(s)
        if rate >= 0.9 and s.nunique(dropna=True) > 5:
            parsed = s if pd.api.types.is_datetime64_any_dtype(s) else pd.to_datetime(s, errors="coerce", format="mixed")
            wd = parsed.dt.day_name().value_counts()
            print(f"  {c!r}: looks like a DATE  parse_rate={rate:.0%}  range={lo.date() if lo is not None else '?'}..{hi.date() if hi is not None else '?'}  distinct={parsed.nunique():,}")
            print(f"      weekdays present: {', '.join(f'{k}={v:,}' for k, v in wd.items())}")
            if len(wd) == 1:
                print("      -> every row falls on one weekday: this is WEEKLY data. Declare granularity='week'.")
            continue
        if (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)) and 1 < s.nunique(dropna=True) <= 2000:
            vc = s.value_counts(dropna=True)
            print(f"  {c!r}: looks CATEGORICAL (candidate market column)  distinct={len(vc):,}")
            print(f"      top {min(TOP_VALUES, len(vc))} by row count: " + ", ".join(f"{k!s}={v:,}" for k, v in vc.head(TOP_VALUES).items()))
            junk = [v for v in vc.index if str(v).strip().lower() in {"total", "unknown", "(not set)", "other", "n/a", "grand total"} or str(v).lower().startswith("total")]
            if junk:
                print(f"      -> junk-looking values present: {junk} (drop them in the transform, report their share)")
            continue
        if pd.api.types.is_numeric_dtype(s):
            d = s.describe()
            print(f"  {c!r}: NUMERIC  min={d['min']:,.2f}  median={d['50%']:,.2f}  max={d['max']:,.2f}  zeros={int((s == 0).sum()):,}  negatives={int((s < 0).sum()):,}")
            continue
        if pd.api.types.is_object_dtype(s):
            stripped = s.astype(str).str.replace(r"[\$,€£%\s]", "", regex=True)
            num_rate = float(pd.to_numeric(stripped, errors="coerce").notna().mean())
            if num_rate > 0.9:
                print(f"  {c!r}: NUMERIC-AS-TEXT (currency/thousands separators)  castable={num_rate:.0%} -> use to_number()")
    return 0


if __name__ == "__main__":
    sys.exit(main())
