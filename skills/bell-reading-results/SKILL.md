---
name: bell-reading-results
description: How to report a Bell geo-experiment result without overclaiming — incremental effect, lift with its confidence interval, p-value versus alpha, iCPA/iROAS and what an "Infinity" efficiency really means. Use after a results analysis job succeeds, before writing any summary, chart caption or recommendation for the client.
license: Apache-2.0
metadata:
  source: Korem-consulting/bell-skills
---

Read `references/reading-results.md` in full before writing a single
number. It is the same document the connector serves as
`bell://methodology/reading-results`.

Then structure the readout in this order:

1. **What was tested.** Treated markets, test window, budget, KPI. If the
   dataset carries several KPIs, this readout is for one of them; each KPI
   is its own results job.
2. **The design it was run on.** Its verdict at planning time. A yellow or
   red design is reported alongside the result, not beneath it.
3. **The effect.** Incremental units, then lift as a percentage, each with
   its interval. The interval is the result.
4. **Significance.** p-value against alpha, in words: detected / not
   detected. Not detected is not "no effect".
5. **Efficiency.** iCPA or iROAS with its interval, judged against the
   client's own threshold. A `null` value with a note means no measurable
   incremental effect — say that, never a cost.
6. **Caveats that apply.** Short window, wide interval, data-quality
   warnings from upload, anything the client did against recommendation.

When a result looks surprising, question the data modeling before the
campaign — completeness of the test window, duplicates, granularity — and
say what you checked.

Further reading: <https://www.bellstatistics.com/glossary/confidence-interval>,
`/glossary/p-value`, `/glossary/incremental-cpa`, `/glossary/iroas`, and
Bell's post on reporting results without spin:
<https://www.bellstatistics.com/post/statistically-speaking-how-to-properly-report-a-b-testing-results>.
