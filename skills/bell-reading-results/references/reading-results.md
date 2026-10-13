# Reading a results analysis without overclaiming

After the campaign has run, Bell compares the treated markets against the
synthetic control over the test window. What comes back, and what it does and
does not license you to say.

## The quantities

**`test_diff`** — total incremental effect: observed treated volume minus what
the synthetic control predicted, summed over the test window. In the KPI's own
units.

**`lift`** — `test_diff / total_y_pred_test`. The incremental effect as a
fraction of what would have happened anyway. Report it as a percentage.

**Confidence interval** — `lower_bound_lift` and `upper_bound_lift` bound the
same ratio. Always report the interval alongside the point estimate. A lift of
12% with an interval spanning −4% to +28% is not a 12% lift; it is a result
consistent with no effect.

**`pvalue`** — two-sided, from the bootstrap null distribution:
`min(2 × min(p_less, p_more), 1.0)`. It is the probability of seeing an effect
this large if the campaign did nothing.

**Efficiency** — one of two metrics, chosen when the analysis is requested:

| Metric | Formula | Direction |
|---|---|---|
| `iCPA` | `budget / test_diff` | cost per incremental action — **lower is better** |
| `iROAS` | `test_diff / budget` | return per unit spent — **higher is better** |

`lower_bound_eff` and `upper_bound_eff` bound it. Judge it against the client's
own threshold, not against zero.

## The Infinity trap

`efficiencyValue` and the CI bounds can arrive as the **strings** `"Infinity"`
or `"-Infinity"`, not as numbers. Bell emits this when `test_diff` has the wrong
sign for the metric — an iCPA where the campaign produced no measurable
incremental volume has no finite cost per action.

It means "no measurable incremental effect", **not** an enormous cost. Never
report it as a number, never render it as currency, and never let it into an
average. Say the effect was not measurable and point at the p-value.

## What not to claim

- **A high p-value is not proof of no effect.** It is a failure to detect one.
  The MDE from the design stage says what size of effect the test could have
  detected; an undetected effect smaller than that is entirely consistent.
- **Do not report a point estimate without its interval.** The interval is the
  result; the point estimate is its midpoint.
- **Do not describe a result as causal beyond the treated markets.** The
  estimate is for the markets that ran the campaign, over the window it ran.
- **Do not re-grade the design at results time.** If the design was yellow or
  red, say so alongside the result rather than quietly presenting the numbers
  as if it were green.
- **`duration < 14` periods** produces a short-analysis-period caveat elsewhere
  in Bell. A short test's interval is wide for a reason; do not narrate around it.
