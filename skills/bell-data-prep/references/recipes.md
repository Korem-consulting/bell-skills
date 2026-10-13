# Transform recipes

Each recipe is the edit you make inside the marked block of
`scripts/transform_template.py`. Output is always `date,location,kpi`,
one row per (date, market). Names in ALL CAPS are things you learn from the
inspector or the user.

## A. A plain CSV export that is nearly right

Typical: `Day, Region, Orders, Revenue` from an analytics tool; sometimes
several rows per day-region because the export also carried a `Channel`
column.

```python
df = read_any(SRC)
df = df.rename(columns={"Day": "date", "Region": "location", "Orders": "kpi"})
df["date"] = parse_dates(df["date"])           # ask if MM/DD vs DD/MM is ambiguous
df["kpi"] = to_number(df["kpi"])
df = drop_junk_rows(df, "location")            # Total / Unknown / (not set)
df = df.groupby(["date", "location"], as_index=False)["kpi"].sum()
```

If the file is wide — one column per market — melt first:

```python
df = read_any(SRC)
df = df.melt(id_vars=["Day"], var_name="location", value_name="kpi") \
       .rename(columns={"Day": "date"})
```

## B. A warehouse export

Typical: a SQL dump at (date, state, campaign_id, device, orders, revenue,
spend), millions of rows, sometimes as parquet. Spend is present but is
**not** uploaded — it becomes the `budget` number at results time.

```python
df = read_any(SRC)                             # parquet is fine
df = df.rename(columns={"order_date": "date", "state": "location", "orders": "kpi"})
df["date"] = parse_dates(df["date"])
df["kpi"] = to_number(df["kpi"])
df["location"] = normalize_us_states(df["location"])   # 'CA' -> 'California'
df = drop_junk_rows(df, "location")
df = df.groupby(["date", "location"], as_index=False)["kpi"].sum()
```

Two things to check with the user before aggregating:

- Does every row belong to the KPI under test? A warehouse table often
  mixes order types (returns, subscriptions, B2B). Filter first.
- Is the geography the campaign's targeting unit? If ads target DMAs and
  the table has states, aggregating to state is right; if it has zip
  codes, map zip → DMA before aggregating (the user supplies the mapping;
  Bell's `mode='DMA'` validates the names).

If the export is too large to load at once, aggregate in chunks:

```python
parts = []
for chunk in pd.read_csv(SRC, chunksize=1_000_000, usecols=["order_date", "state", "orders"]):
    chunk = chunk.rename(columns={"order_date": "date", "state": "location", "orders": "kpi"})
    chunk["date"] = parse_dates(chunk["date"])
    parts.append(chunk.groupby(["date", "location"], as_index=False)["kpi"].sum())
df = pd.concat(parts).groupby(["date", "location"], as_index=False)["kpi"].sum()
```

## C. An ad-platform geo report

Typical Google Ads / Meta / TikTok "geographic" report: a header block
above the real header, a `Total` row at the bottom, currency strings
(`$1,234.56`), region names in the platform's own spelling, a `Day` column
and a `Region` or `DMA region` column, one row per campaign.

```python
df = read_any(SRC, skiprows=2)                 # inspector shows how many junk header lines
df = df.rename(columns={"Day": "date", "Region": "location", "Conversions": "kpi"})
df = drop_junk_rows(df, "location")            # drops 'Total: ...' and 'Unknown'
df["date"] = parse_dates(df["date"])
df["kpi"] = to_number(df["kpi"])               # strips $ , %
df["location"] = normalize_us_states(df["location"])
df = df.groupby(["date", "location"], as_index=False)["kpi"].sum()
```

Watch for: platform-reported conversions being attributed, hence the last
few days moving — set `last_mature_date` at registration; DMA names that
differ between platforms (`"New York, NY"` vs `"New York"`) — normalise to
one list and use `mode='DMA'` so Bell flags the stragglers; and a report
that is already filtered to the campaign under test when the KPI should be
**all** conversions in the market, not just the platform's own.

## D. Excel

`read_any` handles `.xlsx`; pass `sheet=` if the workbook has several.
Merged header cells come through as `Unnamed: 3` — rename from the
inspector's output. Excel dates arrive parsed already; do not re-parse
them as strings.

## E. Weekly data

If the inspector shows every date on the same weekday, the data is weekly.
Keep it weekly, declare `granularity='week'` and the matching
`week_start_day` at registration. Do not resample to daily (you would be
inventing rows) and do not aggregate daily data to weekly unless the user
asks for a weekly test.

## F. The GeoLift format

Meta's GeoLift uses `location, time, Y` with `time` as an integer index.
See `bell-from-geolift` for the recipe that maps the index back to dates.
