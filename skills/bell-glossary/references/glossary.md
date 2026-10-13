# Glossary

Bell's terms, as Bell uses them. Where an industry definition differs, Bell's
wins inside this connector.

| Term | Definition |
|---|---|
| **Allocation** | A specific combination of markets selected for treatment in a geo experiment |
| **Bell Score** | Proprietary scoring metric (MDE / Treatment Proportion); lower is better |
| **Block Bootstrap** | Bootstrap method that preserves time series structure; use when data has autocorrelation |
| **DMA** | Designated Market Area; Nielsen's geographic regions for TV markets |
| **Fixed Effects** | Including an intercept term in the synthetic control model |
| **iCPA** | Incremental Cost Per Acquisition; cost to acquire one incremental unit of KPI. Lower is better |
| **iid Bootstrap** | Independent and identically distributed bootstrap; assumes no time correlation |
| **Incrementality** | The causal impact of marketing; what happened because of the treatment vs. what would have happened anyway |
| **iROAS** | Incremental Return on Ad Spend; incremental revenue per dollar spent. Higher is better |
| **MDE** | Minimum Detectable Effect; the smallest lift the experiment can reliably detect |
| **Power** | Probability of detecting a true effect; typically 80% or 90% |
| **Pre-Period** | Time before the experiment starts; used to train the synthetic control model |
| **R-squared (R²)** | Model fit quality; 1.0 = perfect fit, lower = worse fit |
| **Synthetic Control** | Statistical method that creates a weighted combination of control markets to estimate what would have happened to treatment markets without treatment |
| **Treatment Duration** | Length of the experiment in time periods |
| **Treatment Proportion** | Percentage of total KPI volume in the treatment markets |

Two more that appear in results but not in the product glossary:

| Term | Definition |
|---|---|
| **Effective control size** | The number of control markets genuinely contributing weight to the counterfactual, which is usually far below the raw control count |
| **Residual autocorrelation (`res_corr`)** | Lag-1 autocorrelation of the no-treatment residuals. Drives both the design verdict and the choice between iid and block inference |
