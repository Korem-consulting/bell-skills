#!/usr/bin/env python3
"""Transform template: any source -> Bell long format (date,location,kpi).

Copy this file, edit the block marked EDIT, run it, then validate the output:

    python transform.py --src export.csv --out bell_upload.csv
    python validate_long.py bell_upload.csv --date date --location location --kpi kpi

Everything above the EDIT block is a toolbox; everything below it writes the
file. The script never prints rows — only counts, so it is safe to run and
paste the output into a conversation.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

# ── toolbox ────────────────────────────────────────────────────────────────

JUNK_MARKETS = {"total", "unknown", "(not set)", "other", "n/a", "nan", "grand total", ""}

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


def read_any(path: str, sheet=None, **kw) -> pd.DataFrame:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, sheet_name=sheet or 0, **kw)
    if ext in (".parquet", ".pq"):
        return pd.read_parquet(p)
    if ext in (".json", ".jsonl", ".ndjson"):
        return pd.read_json(p, lines=ext != ".json")
    return pd.read_csv(p, sep=None, engine="python", **kw)


def parse_dates(s: pd.Series, dayfirst: bool = False) -> pd.Series:
    """Parse to a plain date. Set dayfirst=True for DD/MM/YYYY sources."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.normalize()
    return pd.to_datetime(s, errors="coerce", dayfirst=dayfirst, format="mixed").dt.normalize()


def to_number(s: pd.Series) -> pd.Series:
    """'$1,234.56' / '1 234' / '12%' -> 1234.56 / 1234 / 12."""
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    cleaned = s.astype(str).str.replace(r"[\$€£,%\s]", "", regex=True).replace({"": None, "nan": None})
    return pd.to_numeric(cleaned, errors="coerce")


def drop_junk_rows(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Remove Total / Unknown / (not set) rows and report what they carried."""
    key = df[col].astype(str).str.strip().str.lower()
    mask = key.isin(JUNK_MARKETS) | key.str.startswith("total")
    if mask.any():
        print(f"dropped {int(mask.sum()):,} junk rows in {col!r}: {sorted(df.loc[mask, col].astype(str).unique().tolist())[:8]}")
    return df.loc[~mask].copy()


def normalize_us_states(s: pd.Series) -> pd.Series:
    """Map 'CA' -> 'California', title-case full names, leave others as-is."""
    stripped = s.astype(str).str.strip()
    upper = stripped.str.upper()
    return upper.map(US_STATES).fillna(stripped.str.title())


# ── EDIT: map your source onto date / location / kpi ───────────────────────

def transform(src: str, last_mature_date: str | None = None) -> pd.DataFrame:
    df = read_any(src)                                   # add skiprows=N / sheet="Data" if needed

    df = df.rename(columns={                             # <- your column names on the left
        "date": "date",
        "location": "location",
        "kpi": "kpi",
    })
    df["date"] = parse_dates(df["date"], dayfirst=False)  # <- True for DD/MM/YYYY exports
    df["kpi"] = to_number(df["kpi"])
    df = drop_junk_rows(df, "location")
    df["location"] = normalize_us_states(df["location"])  # <- remove for non-US markets

    # If the file is wide (one column per market or per date), melt BEFORE the rename:
    # df = df.melt(id_vars=["Day"], var_name="location", value_name="kpi").rename(columns={"Day": "date"})

    # If rows are split by campaign / channel / device, this sum is what makes them one-per-(date, market):
    df = df.dropna(subset=["date"])
    df = df.groupby(["date", "location"], as_index=False)["kpi"].sum()

    if last_mature_date:                                 # or pass last_mature_date at registration instead
        df = df[df["date"] <= pd.Timestamp(last_mature_date)]
    return df[["date", "location", "kpi"]]

# ── end EDIT ───────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--last-mature-date", default=None)
    args = ap.parse_args()

    out = transform(args.src, args.last_mature_date)
    out = out.sort_values(["date", "location"])
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(args.out, index=False)
    print(f"wrote {args.out}: {len(out):,} rows, {out['location'].nunique():,} markets, "
          f"{out['date'].nunique():,} dates ({out['date'].min()}..{out['date'].max()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
