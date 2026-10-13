#!/usr/bin/env python3
"""Validate a long-format file against Bell's data contract, locally.

    python validate_long.py FILE --date COL --location COL --kpi COL
                            [--granularity day|week] [--week-start monday]

Exit 0: would upload and can support an experiment (warnings may still
print). Exit 1: at least one error — fix the transform before uploading.
Prints counts and summaries only, never rows.

Thresholds mirror the engine's upload and design checks, as exposed by the
connector's get_data_requirements. If the tool
and this file disagree, the tool is right and this file needs updating.
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

THRESHOLDS = {
    "day":  {"history_required": 180, "history_recommended": 365, "min_test": 14, "max_test": 180, "unit": "days"},
    "week": {"history_required": 80,  "history_recommended": 100, "min_test": 4,  "max_test": 26,  "unit": "weeks"},
}
MIN_MARKETS, RECOMMENDED_MARKETS, MAX_MARKETS = 3, 10, 500
PRE_TO_DURATION = 10
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--date", required=True)
    ap.add_argument("--location", required=True)
    ap.add_argument("--kpi", required=True)
    ap.add_argument("--granularity", choices=["day", "week"], default="day")
    ap.add_argument("--week-start", default="monday", choices=WEEKDAYS)
    args = ap.parse_args()

    errors, warnings = [], []
    df = pd.read_csv(args.file)

    for col in (args.date, args.location, args.kpi):
        if col not in df.columns:
            errors.append(f"column {col!r} not in file (columns: {list(df.columns)})")
    if errors:
        _report(errors, warnings)
        return 1

    dates = pd.to_datetime(df[args.date], errors="coerce", format="mixed")
    bad_dates = int(dates.isna().sum())
    if bad_dates:
        errors.append(f"{bad_dates:,} rows have an unparseable date")

    kpi = pd.to_numeric(df[args.kpi], errors="coerce")
    bad_kpi = int(kpi.isna().sum() - df[args.kpi].isna().sum())
    null_kpi = int(df[args.kpi].isna().sum())
    if bad_kpi:
        errors.append(f"{bad_kpi:,} KPI values are not numeric (strip currency symbols / separators)")
    if null_kpi:
        warnings.append(f"{null_kpi:,} KPI values are empty; Bell will treat missing pairs as zero")
    neg = int((kpi < 0).sum())
    if neg:
        warnings.append(f"{neg:,} negative KPI values — refunds or corrections? Confirm they belong in the KPI")

    loc = df[args.location].astype(str).str.strip()
    blank_loc = int(((loc == "") | df[args.location].isna() | (loc.str.lower() == "nan")).sum())
    if blank_loc:
        errors.append(f"{blank_loc:,} rows have a blank market")
    junk = sorted(v for v in loc.unique() if v.lower() in {"total", "unknown", "(not set)", "other", "n/a", "nan", "grand total"} or v.lower().startswith("total"))
    if junk:
        errors.append(f"junk market values present: {junk} — drop them in the transform")

    # one row per (date, market)
    dup = df.assign(_d=dates, _l=loc).groupby(["_d", "_l"]).size()
    n_dup_pairs = int((dup > 1).sum())
    if n_dup_pairs:
        errors.append(f"{n_dup_pairs:,} (date, market) pairs appear more than once — aggregate (sum) before uploading")

    # granularity
    valid = dates.dropna()
    weekdays = valid.dt.day_name().str.lower().unique().tolist()
    if len(weekdays) == 1 and args.granularity == "day":
        errors.append(f"every date is a {weekdays[0].title()}: the data is weekly, but --granularity day was declared")
    if len(weekdays) > 1 and args.granularity == "week":
        errors.append("dates fall on several weekdays but --granularity week was declared; weekly rows must all share one weekday")
    if len(weekdays) == 1 and args.granularity == "week" and weekdays[0] != args.week_start:
        errors.append(f"weekly rows fall on {weekdays[0].title()} but --week-start {args.week_start} was declared")

    # markets (junk values are already an error above; keep them out of the counts)
    junk_set = set(junk)
    real = ~loc.isin(junk_set) & (loc != "")
    n_markets = int(loc[real].nunique())
    if n_markets < MIN_MARKETS:
        errors.append(f"{n_markets} markets; a geo experiment needs at least {MIN_MARKETS}")
    elif n_markets > MAX_MARKETS:
        errors.append(f"{n_markets:,} markets exceeds the {MAX_MARKETS} maximum — aggregate up (city→state, zip→DMA)")
    elif n_markets < RECOMMENDED_MARKETS:
        warnings.append(f"{n_markets} markets is legal but below the {RECOMMENDED_MARKETS} recommended; the synthetic control has little to blend")

    # history and test duration
    t = THRESHOLDS[args.granularity]
    n_periods = int(valid.nunique())
    longest = max(0, min(t["max_test"], n_periods // PRE_TO_DURATION))
    if longest < t["min_test"]:
        errors.append(f"{n_periods} {t['unit']} of history supports a test of at most {longest} {t['unit']}, below Bell's {t['min_test']}-{t['unit'][:-1]} minimum; add earlier history (≥{t['min_test'] * PRE_TO_DURATION} {t['unit']})")
    elif n_periods < t["history_required"]:
        warnings.append(f"{n_periods} {t['unit']} of history is under the {t['history_required']} floor Bell enforces at upload; expect rejection unless more history is added")
        errors.append(f"history below Bell's required {t['history_required']} {t['unit']} (have {n_periods})")
    elif n_periods < t["history_recommended"]:
        warnings.append(f"{n_periods} {t['unit']} of history clears the floor but is under the {t['history_recommended']} recommended; longest test supported: {longest} {t['unit']}")

    # grid completeness (silent zero-fill)
    if n_markets and n_periods:
        expected = n_markets * n_periods
        grid = df.assign(_d=dates, _l=loc)[real].dropna(subset=["_d"])
        present = int(grid.groupby(["_d", "_l"]).ngroups)
        missing = expected - present
        if missing > 0:
            per_market = grid.groupby("_l")["_d"].nunique().reindex(sorted(loc[real].unique()), fill_value=0)
            worst = per_market.sort_values().head(5)
            pct = missing / expected
            msg = (f"{missing:,} of {expected:,} (date, market) pairs are missing ({pct:.1%}) and will be ZERO-FILLED silently by Bell; "
                   f"least complete markets: " + ", ".join(f"{k}={v}/{n_periods}" for k, v in worst.items()))
            (errors if pct > 0.20 else warnings).append(msg)

    # markets that are mostly zero (only meaningful once the KPI parses)
    if n_markets and not bad_kpi:
        zero_share = df.assign(_k=kpi.fillna(0), _l=loc)[real].groupby("_l")["_k"].apply(lambda s: float((s == 0).mean()))
        mostly_zero = zero_share[zero_share > 0.5]
        if len(mostly_zero):
            warnings.append(f"{len(mostly_zero)} market(s) are zero on more than half their days: {list(mostly_zero.index[:8])} — real, or missing data?")

    print(f"file: {args.file}")
    print(f"rows={len(df):,}  markets={n_markets:,}  periods={n_periods:,} {t['unit']}  range={valid.min().date() if len(valid) else '?'}..{valid.max().date() if len(valid) else '?'}")
    print(f"declared granularity={args.granularity}  weekdays present={len(weekdays)}  longest test supported={longest} {t['unit']}")
    _report(errors, warnings)
    return 1 if errors else 0


def _report(errors, warnings):
    for w in warnings:
        print(f"WARNING  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    if not errors and not warnings:
        print("OK       no issues found")
    elif not errors:
        print("OK       no blocking errors; review the warnings with the user")
    else:
        print(f"FAIL     {len(errors)} error(s) — fix the transform before uploading")


if __name__ == "__main__":
    sys.exit(main())
