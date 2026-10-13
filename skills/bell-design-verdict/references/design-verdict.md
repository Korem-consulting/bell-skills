# Is this design sound?

Bell scores a candidate design by penalty points. Zero points is green, one is
yellow, two or more is red. Report the verdict and its reasons; do not invent a
grade of your own from the raw numbers.

## The three penalties

**Historical fit (A/A p-value).** Bell runs the design over a window where no
treatment happened and checks whether the synthetic control reproduces the
treated markets there.

| A/A p-value | Points | Reason reported |
|---|---|---|
| `< 0.05` | 2 | "The counterfactual does not reproduce the treated markets' historical behavior reliably during the no-treatment period." |
| `< 0.10` | 1 | "The counterfactual shows a moderate difference from the treated markets' historical behavior during the no-treatment period." |
| otherwise | 0 | — |

**Residual autocorrelation.** Lag-1 autocorrelation of the no-treatment residuals.

| `res_corr` | Points | Reason reported |
|---|---|---|
| `>= 0.30` | 2 | "Residuals have high autocorrelation (above 0.3) during the no-treatment period." |
| `>= 0.15` | 1 | "Residuals have moderate autocorrelation (between 0.15 and 0.3) during the no-treatment period." |
| otherwise | 0 | — |

**History length.** One point when `n_periods < max(n_controls, 3 × effective_control_size)`:
"Given the effective number of control markets contributing to this design's
counterfactual, more historical data is needed for a reliable analysis."

Note `effective_control_size`, not the raw control count. A design drawing on
forty markets where three carry nearly all the weight needs history for three.

## The verdict

| Points | Verdict | Summary reported |
|---|---|---|
| 0 | **green** | "The design is well suited for reliable analysis." |
| 1 | **yellow** | "The design is usable, but stronger alternatives should be considered if possible." |
| 2+ | **red** | "The design is not suited for reliable analysis." |

A green design also reports "Historical fit is reliable, Residual
autocorrelation is low, and sufficient historical data is available."

## Ignore the other verdict

A second field also called `verdict` exists, with values `strong` / `moderate` /
`weak`. It is computed from R² alone — `> 0.99` strong, `> 0.95` moderate, else
weak — and it knows nothing about historical fit, autocorrelation or history
length.

**The green/yellow/red classifier above is the canonical one.** The two can
disagree on the same design, and a high R² regularly accompanies a red verdict.
Never report the R²-only value, and never blend the two into a single judgement.

## Reading the numbers behind it

- **MDE** — the smallest effect this design could reliably detect, in the KPI's
  own units. An MDE larger than the lift the client expects means the test
  cannot answer their question, whatever the verdict says. Say so.
- **R²** — how well the synthetic control tracks the treated markets. Useful
  context, not a verdict.
- **Treatment proportion** — share of total KPI volume in the treated markets.
  Bell expects 10–80%.
- **`res_corr`** — also selects the inference method: with `inference_type='auto'`,
  Bell uses `iid` when `res_corr < 0.15` and `block` otherwise. Leave it on
  `auto` unless you know why not.
