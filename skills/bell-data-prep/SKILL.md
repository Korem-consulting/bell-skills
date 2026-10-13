---
name: bell-data-prep
description: Prepare a client's marketing data for a Bell geo experiment without ever reading their rows — inspect the header and a bounded sample, write a pandas transform, validate locally against Bell's data contract, then upload and register. Covers CSV, Excel, warehouse exports and ad-platform geo reports. Use before any upload to Bell, whenever an upload is rejected, or when the user shares a data file.
license: Apache-2.0
metadata:
  source: Korem-consulting/bell-skills
---

# Preparing data for Bell

## The one rule

**A client's rows never enter this conversation.** Not to "get a feel for
it", not to check a date format, not because the file is small. You read
the header and a bounded sample through the inspector, you write a
transform, you run it, you validate the output, you upload the output.

A model that opens the CSV to understand it has already failed: the data
is now in the transcript, the context is spent on rows instead of
judgment, and the approach stops working the moment the file is large.
The script approach works the same for 500 rows and 50 million.

This is also why the transform is always **Python + pandas**, never a
manual edit and never "I'll paste the cleaned version": the script is the
audit trail, it can be re-run when the campaign ends and the test window
must be appended, and it makes every source — CSV, Excel, a warehouse
dump, a Google Ads geo report — the same job.

## What Bell needs

Call `get_data_requirements` first; it returns the live contract. In
short, per `granularity`:

| | daily | weekly |
|---|---|---|
| Format | long CSV: one row per (date, market), one KPI column | same |
| History required / recommended | 180 / 365 days | 80 / 100 weeks |
| Test duration allowed | 14–180 days | 4–26 weeks |
| History per period of test | 10× (a 28-day test needs ≥280 days) | 10× |
| Markets | 3 minimum (hard), 10+ recommended, 500 maximum (hard) | same |

Hard rules the engine rejects on: **exactly one row per (date, market)**;
numeric KPI; declared granularity must match how the rows are actually
aggregated (rows all on one weekday = weekly). One KPI per upload; spend is
not a column — it enters later as a single budget number.

Silent behaviour to design around: a **missing (date, market) pair is
filled with zero, without warning.** A market that has no rows for a
fortnight reads as a fortnight of zero sales.

Column names are free; you pass them at registration.

## The loop

### 1. Inspect — bounded, by script

```bash
python scripts/inspect_source.py <file> [--sheet NAME] [--sample 20]
```

Prints shape, columns with dtype / null count / distinct count, up to 20
sample rows, and for likely date and market columns: parse rate, range,
weekday spread, top values. It **cannot** print more than the sample. Use
it on the raw file and again on your transform's output.

Decide from the output: which column is the date, which is the market,
which is the KPI; whether rows are already one-per-(date, market) or split
by campaign / channel / device / product; whether the data is daily or
weekly; whether market names are consistent; whether recent dates look
immature.

Ask the user the business questions the file cannot answer: which KPI the
test is about, what geographic unit the campaign is targeted at, whether
recent days are still being attributed.

### 2. Transform — pandas, from the template

Copy `scripts/transform_template.py`, edit the marked block, run it. The
template already: reads csv/xlsx/parquet, parses dates, strips currency
and thousands separators, drops total/unknown rows, normalises market
names, **aggregates by (date, market)**, optionally cuts at a maturity
date, and writes `date,location,kpi`. Recipes for the three common
sources are in `references/recipes.md`; the GeoLift format is in
`bell-from-geolift`.

Aggregation is a sum for volume KPIs (orders, revenue, installs, leads)
and never the right thing for rates (CVR, CPA, ROAS). If the client's KPI
is a rate, test the numerator — say why.

### 3. Validate — locally, before upload

```bash
python scripts/validate_long.py out.csv --date date --location location --kpi kpi --granularity day
```

Reproduces the engine's checks: duplicates, non-numeric KPI, inferred
granularity vs declared, history floors, longest test supported, market
count, grid completeness (how many (date, market) pairs are missing and
would be zero-filled), negative values, and markets that are mostly zero.
Exit code 1 means the upload would fail or the experiment could not run.
Fix the transform and re-run; do not upload a file that fails.

**Go through the warnings with the user.** Some are decisions, not bugs: a
market with 40% missing days may be dropped, or kept because it is the
one they want to test; a 200-day history is legal but caps the test at 20
days. Say what each warning means for the experiment and let them choose.

### 4. Upload and register

```
create_dataset_upload  → upload_url + file_ref
curl -sS -X PUT --upload-file out.csv '<upload_url>'
register_dataset(file_ref, time_col, location_col, kpi_col, granularity, mode, week_start_day, last_mature_date, original_filename)
```

If curl cannot connect at all — "could not resolve host", connection
refused or reset, or a proxy refusing the host — you are in a sandbox that
blocks outbound traffic, as Claude.ai's code execution does by default.
Don't look for another route, and don't read the file into the
conversation. Tell the user the one-time fix, naming the host from
`upload_url` (normally `api.bellstatistics.com`): *Settings → Capabilities
→ Code execution and file creation → Additional allowed domains*, add the
host, then ask again. On a Team or Enterprise plan an org admin may have to
allow it. The tool's `if_upload_is_blocked` field has the exact wording.
Offer the alternative in the same breath: upload the file in the Bell app,
then pick it up here with `list_datasets`.

An HTTP error from Bell itself is different, and comes back as JSON: 403
means the link expired and 409 that it was already used. For either, call
`create_dataset_upload` again (after a 409, first check whether that
`file_ref` registers).

`mode='USA'` for US states, `'DMA'` for Nielsen DMAs, `'OTHER'` for
anything else — USA/DMA only add naming warnings, they never block.
`granularity='week'` only if the rows are already weekly; pass
`week_start_day` to match the weekday they fall on. `last_mature_date`
trims the immature tail without editing the file.

The response carries the `dataset_id` you will use from here on, a
`data_summary`, `issues` (the same checks as the validator, run on what
Bell actually stored), and the `test_duration_range` the data supports.
Read the issues with the user before proposing a design.

### 5. After the campaign

The results analysis needs pre-period **and** test window in the same
dataset. Re-run the same transform on the extended export, validate, and
upload it as a new dataset. The script you kept in step 2 is what makes
this a two-minute job.

## Edge cases and what to do

| Situation | Do |
|---|---|
| Rows split by campaign / channel / device / product | Sum to (date, market). Confirm with the user that all rows belong to the KPI being tested. |
| Wide file: one column per market | `melt` to long. |
| Wide file: one column per date | `melt` the other way. |
| Mixed "CA" and "California" | Normalise to one form (the template maps US abbreviations to names). Never let both survive; Bell would treat them as two markets. |
| "Unknown", "Total", "(not set)", "Other" rows | Drop, and tell the user how much volume they carried. If it is more than a few percent, that is a finding, not a footnote. |
| Currency strings, thousands separators, percentages | Strip and cast; the template does. |
| Dates in `MM/DD/YYYY` vs `DD/MM/YYYY` | Check the inspector's parse rate and range under each assumption; ask if ambiguous. |
| Weekly data | Declare `week` and the right `week_start_day`. Do not resample daily to weekly unless the user asks — it discards resolution. |
| Gaps in the grid | Decide together: drop the market, or accept zero-fill knowing it biases that market down. Never silently accept. |
| Recent days look low | Attribution lag. Set `last_mature_date` rather than trimming the file. |
| Outliers | Do not remove them by default. Show them aggregated (the inspector's top values, a per-market summary), ask what happened those days, and record the decision. Bell's note on outliers: <https://www.bellstatistics.com/post/when-one-bad-apple-spoils-the-barrel-tackling-outliers-in-a-b-testing>. |
| More than 500 markets | Aggregate up (zip → DMA, city → state). |
| Fewer than 3 markets | A geo experiment is not possible. Say so. |
| Multiple KPIs | One file per KPI, or one file with several KPI columns if the connector's register step lists them — check `get_data_requirements`. Test the primary first. |
| `curl` can't reach the upload host (sandbox network block) | Have the user allow the host in their code-execution settings, or upload in the Bell app and use `list_datasets`. See step 4. |
| Still stuck after two rounds | Escalate per `bell-geo-experiments`: summary + validator output, no rows. |

## For the engineer reading this

The contract is mirrored from the engine's upload and design checks:
history floors and duration bounds, the 10:1 rule, duplicate detection and
the weekly-aggregation check. `get_data_requirements` is the live version; if the two disagree, the tool
wins and this skill needs a fix. The validator's thresholds live at the
top of `scripts/validate_long.py` and match the tool's `thresholds` block.
