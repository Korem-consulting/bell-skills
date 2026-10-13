# What actually goes wrong

The failures below account for most rejected uploads and most confused results.
Each carries the engine's real error text, so you can recognise it and say what
to do rather than guessing.

## Duplicate (date, location) pairs — the most common rejection

Bell needs exactly one row per date per market. Data joined from two sources, or
split by campaign, channel or device, produces several.

```
Some (Date, Location) pairs, like (2024-03-01, California), appear multiple times in the data. Please aggregate the data so that each (Date, Location) pair appears only once.
```

**Fix:** group by date and location and sum the KPI, before uploading. Do not
ask the client to fix it by hand, and do not read their rows into the
conversation to inspect them — write a transform, run it, upload the output.

## Weekly data declared as daily

If every date in the file falls on the same weekday, the data is already
aggregated weekly.

```
Input mismatch: data appears to be aggregated weekly, but granularity='day' was provided. Set granularity='week' or provide daily data.
```

And when the week does not start on the declared day:

```
Input data appears to be aggregated weekly on Monday, which does not match the specified week_starts_on: Sunday. Please adjust your data or the week_starts_on parameter.
```

**Fix:** check the distinct weekdays present before choosing `granularity`.
One distinct weekday means weekly.

## Not enough history

Bell requires a long pre-period to fit the synthetic control, and the test
duration must be at most one tenth of the available history. Call
`get_data_requirements` for the exact floors — they differ by granularity — and
check them *before* proposing a duration, not after the analysis is rejected.

A design whose duration is too long for the history available is rejected
outright; one that only just fits produces a weak counterfactual and a red
verdict.

## Too few markets, or one market dominating

The synthetic control is a weighted blend of untreated markets. Too few markets
leaves nothing to blend; a single dominant market means the "blend" is really
one market. This surfaces as `effective_control_size` far below the raw control
count, and it drives the history-length penalty in the design verdict.

## An empty dataset list

`list_datasets` shows the datasets the client's organization owns — both the
ones uploaded through the connector or the API and the ones created in the Bell
app. An empty list is therefore meaningful now, but it is still worth asking
before concluding it: the client may be holding a token issued to a different
organization.

One thing that trips people up: the 24-hour expiry applies to the *upload
token*, not to the data. An upload the client owns stays in Bell and keeps its
stable `dataset_id`; only the temporary alias stops resolving. Do not tell a
client their data will disappear overnight.
