---
name: bell-from-geolift
description: For teams who already run Meta's open-source GeoLift (R package) and are moving to, or comparing with, Bell — maps GeoLift's functions and parameters to Bell's tools, converts a GeoLift-format dataset (location, time, Y) to Bell's, and explains where the two methods differ and why the numbers will not match. Use when a user mentions GeoLift, GeoLiftMarketSelection, GeoLiftPower, lookback_window, or asks why Bell's MDE, budget or p-value differs from GeoLift's.
license: Apache-2.0
metadata:
  source: Korem-consulting/bell-skills
---

# Coming from GeoLift

GeoLift is a well-built implementation of synthetic control with unusually
good planning tooling. Bell uses the same family of method, so most of what
a GeoLift user knows carries over. This skill is about the parts that
don't. Be cooperative: nobody is wrong for having used GeoLift, and a team
comparing the two deserves a straight answer about why numbers differ.

Bell's public explainer: <https://www.bellstatistics.com/glossary/geolift>.

## Concept and parameter map

| GeoLift | Bell | Notes |
|---|---|---|
| `GeoDataRead()` | `bell-data-prep` → `register_dataset` | Bell keeps real dates; GeoLift replaces them with an integer `time` index. |
| `Y_id`, `location_id`, `time_id` | `kpi_col`, `location_col`, `time_col` | Free names on both sides. |
| `GeoLiftMarketSelection()` | `start_allocation_search` | Bell searches by **treatment share of volume**, not by number of markets; see "Different search objective". |
| `treatment_periods` | `duration` | Same unit: the dataset's own periods. |
| `N` (markets to treat) | not an input | Bell chooses the count within the volume range you give. |
| `effect_size` grid | not an input | Bell returns the MDE; you compare it to the lift you expect. |
| `cpic` | `budget` from the design, `efficiency_threshold` for the target | Bell derives required budget from the MDE rather than assuming a cost per incremental conversion. |
| `lookback_window` | not an input | Bell fits over the full history and cross-validates; see "Budget estimation". |
| `alpha` | `alpha` (results); design uses Bell's verdict | Default 0.1 in Bell's results tool. |
| `GeoLiftPower()` / `GeoLiftPowerFinder()` | `start_design_analysis` | Returns MDE, budget, R², and a green/yellow/red verdict with reasons. |
| `GeoLift()` | `start_results_analysis` | One job per KPI. |
| `inference_type` (Bell) | — | `auto` picks iid vs block bootstrap from residual autocorrelation. Leave it. |
| `fixed_effects` | default handled | Bell's synthetic control includes an intercept; weights are not forced to sum to one. |
| `include_markets` / `exclude_markets` | same names | |

## Converting a GeoLift dataset

GeoLift's `GeoDataRead` output is `location, time, Y` where `time` is
`1..T`. Bell needs the calendar back. If you still have the original file
GeoLift read, transform **that** with `bell-data-prep` instead. Otherwise
map the index to dates from the known start date and cadence:

```python
df = read_any("geolift_data.csv")                  # location, time, Y
start = pd.Timestamp("2024-01-01")                 # the first date GeoLift saw — ask
step = pd.Timedelta(days=1)                        # or weeks=1 for weekly
df["date"] = start + (df["time"].astype(int) - 1) * step
df = df.rename(columns={"location": "location", "Y": "kpi"})[["date", "location", "kpi"]]
```

Then validate as usual. Two traps: GeoLift tolerates a location missing
some periods more quietly than Bell (Bell zero-fills — check the grid),
and GeoLift's `time` index hides whether the data was daily or weekly, so
confirm the cadence with the user before declaring `granularity`.

## Where the methods differ, and what you'll see

These are Bell's methodology team's observations about GeoLift as
documented and implemented. Each is stated with the consequence a client
would notice.

1. **The test statistic.** For two-sided tests GeoLift sums the
   *absolute* daily residuals (treated minus synthetic control) over the
   test period; Bell sums the residuals themselves. The sum of absolute
   residuals has no business meaning — it is not the incremental volume
   — and it makes GeoLift's confidence intervals wider than the effect
   warrants. A visible symptom: GeoLift's intervals for lift, iCPA and
   iROAS stop narrowing as the test runs longer, plateauing at a width
   that is often too wide to act on. Bell's intervals keep narrowing with
   duration.

2. **Test-period variance and alpha.** GeoLift fits the synthetic-control
   weights on the pre-period only, then compares the test-period residuals
   against a pre-period null distribution. Test-period residuals are
   naturally larger than in-sample ones, so the null is too tight: GeoLift
   tends to **underestimate the budget** a test needs and to report
   **p-values biased downward**. (The two effects — wider intervals from
   item 1, over-tight null here — pull in opposite directions; in practice
   GeoLift's intervals still end up wider than they should be.) Bell
   cross-validates over held-out folds, which is why its budget estimates
   run higher and its verdict can be red where GeoLift said go.

3. **Budget estimation anchored on the last pre-period.** GeoLift's power
   simulation is driven by the final pre-treatment window, so allocations
   whose late residuals happen to be noisy look "significant" at a
   smaller simulated budget and get favoured. `lookback_window` softens
   this, but the lookback samples overlap heavily. Bell's design analysis
   uses the whole history through cross-validation.

4. **Different search objective for market selection.** GeoLift favours
   treatment markets that correlate with *each other*. What matters is how
   well the *control* markets predict the treatment group — and GeoLift's
   objective often returns allocations worse than random ones. Bell's
   allocation search optimises the counterfactual fit for a given
   treatment share of volume. Expect Bell to recommend different markets;
   the design analysis, not either tool's ranking, is what settles it.

5. **Weights constrained to sum to one.** GeoLift's synthetic control is a
   convex combination of donors, so it cannot fit a treatment group whose
   scale exceeds the donors'. Texas as the only treated market against the
   other 49 states is a poor fit by construction. Bell does not impose the
   constraint; large-market tests remain feasible. If a client's GeoLift
   power analysis "couldn't find a design" for their biggest markets, this
   is usually why.

6. **Heuristic allocation ranking.** GeoLift ranks candidate allocations
   by averaging the ranks of three simulation metrics (`EffectSize`,
   `pvalue`, `abs_lift_in_zero`). The rule is arbitrary and rarely aligned
   with the business question. Bell ranks by MDE relative to treatment
   share (the Bell Score) and then makes you run the design analysis
   anyway.

7. **Homoskedastic residuals.** GeoLift treats residual variance as
   constant over time; in marketing data it usually scales with volume.
   Bell's `inference_type='auto'` chooses a block bootstrap when residuals
   are autocorrelated and the verdict penalises high autocorrelation
   outright, so a design that would have looked fine under a constant-
   variance assumption gets flagged.

**What this means for a comparison:** Bell will typically report a higher
required budget, a wider-then-narrower interval, a less flattering
p-value, and different recommended markets. None of that is a bug on
either side; it is what the items above predict. Do not "reconcile" the
numbers by picking the friendlier one.

## Best practices carried over

- **Always look at the plot before trusting a fit.** Whether it is
  GeoLift's `GeoPlot` or Bell's design visualisations, a synthetic control
  that tracks the treated markets in the pre-period is the entire premise.
  Verify the history "looks OK" — no level shifts, no missing stretches,
  no single dominant donor — before reading any number.
- **Keep the donor pool genuinely untreated.** Check the media plan, not
  the correlation matrix. A market receiving spillover fits especially
  well and corrupts the counterfactual.
- **Enough history, and ten times the test length.** GeoLift will run on
  less; Bell refuses, on purpose.
- **Confidence interval first, point estimate second**, in both tools.

## Where Bell is confident it does better

Say this much and no more: Bell's estimator targets the
incremental volume directly, validates designs out of sample, does not
constrain weights to sum to one, and searches allocations by
counterfactual fit.

## For the engineer

GeoLift documentation: <https://facebookincubator.github.io/GeoLift/docs/GettingStarted/Walkthrough>
and its confidence-interval note
<https://facebookincubator.github.io/GeoLift/docs/Methodology/Confidence_Interval_Explanation/>.
The observations above are Bell's; where they describe GeoLift's
implementation they refer to the package as of 2026 and may change.
