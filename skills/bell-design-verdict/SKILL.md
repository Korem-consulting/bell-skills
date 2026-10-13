---
name: bell-design-verdict
description: How to judge whether a Bell geo-experiment design is sound. Explains the green/yellow/red verdict (historical fit, residual autocorrelation, history length), why the R²-only "strong/moderate/weak" verdict must be ignored, and how to read MDE, budget, R² and treatment proportion. Use after a design analysis or allocation search returns, before telling a client whether to run the test.
license: Apache-2.0
metadata:
  source: Korem-consulting/bell-skills
---

Read `references/design-verdict.md` in full before reporting a design.
It is the same document the connector serves as `bell://methodology/design-verdict`.

Then, in the readout:

1. Give the verdict word (green / yellow / red) and every reason string it
   came with, unedited.
2. Give the MDE in the KPI's own units and compare it to the lift the
   client expects. If the MDE is larger, say the test cannot answer their
   question, whatever the verdict.
3. Give the required budget, and say it is the spend at which the MDE
   becomes detectable — not a recommendation to spend that much.
4. If the client asks about R², explain it as fit context, and that the
   green/yellow/red verdict already accounts for it.

An allocation recommendation is a candidate, not a design. Run
`start_design_analysis` on the chosen markets before quoting an MDE.
