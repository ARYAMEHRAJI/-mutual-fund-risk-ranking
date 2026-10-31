# Methodology and research decisions

## Universe
The current universe follows the notebook filters: active schemes, Direct plan, Growth option, Open Ended Schemes, and at least three years of history. The most recent metadata NAV date is used as the reference; hard-coded dates are avoided. Active status does not guarantee a fresh NAV, so stale NAV checks remain a required validation step.

## NAV validation
Missing identifiers, invalid dates, non-numeric NAV, and non-positive NAV rows are removed. Duplicate scheme/date rows retain the last source row. Only strongly evidenced persistent decimal-scale shifts or isolated one-day spikes are corrected. Every correction is exported to cleaning_audit.csv. Ambiguous anomalies remain untouched.

## Returns
Period returns compare the latest NAV with the last available NAV on or before the calendar reference date (1, 3, 6, or 12 months before the latest date). Missing history remains missing.

## Risk metrics
- Annualised volatility: sample standard deviation of daily NAV returns multiplied by sqrt(252).
- Maximum drawdown: minimum NAV / running peak - 1 over the available history.
- Sharpe: annualised arithmetic mean daily return less the annual risk-free rate, divided by annualised volatility. The notebook's final reconstruction used a zero risk-free rate; this is the default and can be configured.
- Sortino: annualised arithmetic mean return less the risk-free rate, divided by target-zero downside deviation. Downside deviation is sqrt(mean(min(daily return, 0)^2)) multiplied by sqrt(252). Positive days contribute zero to the mean-square denominator.
- Stability guardrail: Sharpe is not reported when annualised volatility is below 0.5%; Sortino is not reported when annualised downside deviation is below 0.5%. Ratios with near-zero denominators can become extremely large and unstable, particularly for Overnight and Liquid funds. These values remain missing and are handled through the existing metric-weight coverage mechanism. The floor is configurable with MIN_ANNUALIZED_RISK_DENOMINATOR.

These are arithmetic annualisations, not geometric CAGR estimates.

## Peer scoring
Each metric is converted to a 0-100 percentile within a peer group. Higher returns, Sharpe, Sortino, and less-negative drawdown receive higher scores. Lower volatility receives a higher score. The implementation prefers category_sub as the peer group and falls back to category_group_clean. A final group must contain at least five funds to receive percentile scores or ranks. Smaller groups remain in the dataset with ranking_group_status='insufficient_peers'; their descriptive metrics are retained, but their relative ranks are suppressed.

## Composite ranking
The four profile weights are carried forward from the research notebook and each totals 100. Only valid metric scores contribute. The weighted score is divided by the sum of available weights. coverage_* reports the available original weight mass (0-100). If no metric score is valid, the composite and rank remain missing.

## Evaluation
The in-sample diagnostic compares composite scores with trailing 12-month returns. Since trailing 12-month return is itself a model input, this is a consistency diagnostic and not independent predictive validation.
The pipeline also performs rolling out-of-sample tests. At each historical formation date, raw NAV observations are first truncated at that date and anomaly detection/cleaning is rerun on that truncated history only. Metrics, peer scores, and composite rankings therefore cannot use future NAV observations or future anomaly evidence. Forward-period NAV is cleaned separately through the evaluation date solely to measure the outcome; it is never passed into formation-date feature calculation. The formation NAV used as the investment starting value comes from the formation-time cleaned history.

The historical universe and classifications still use the latest available eligible-fund metadata. Consequently, funds that have since closed or disappeared may be absent from historical windows, and current categories may differ from historical categories. This leaves survivorship and taxonomy look-ahead bias. The evaluation is now point-in-time with respect to NAV-derived features and cleaning, but it is not a fully point-in-time universe/backtest.

## Questionnaire
The ten answers are each between 0 and 10. The weighted score is normalised as 100 * sum(answer_i * weight_i) / (10 * sum(weights)). This corrects the notebook's interim division-by-two normalisation.

## Limitations
Percentiles depend on the selected universe; broad subcategories can still contain different strategies. NAV-only data does not capture every fee, tax, liquidity, or manager factor. Historical results do not predict future performance.


### Top-N overlap interpretation
Top-N overlap is reported only when the peer group contains more funds than the requested N. If N would include every eligible fund in a group, overlap is left missing rather than reported as 100%; such a result would be mechanically guaranteed and would overstate selection quality. Spearman correlation can still be reported for groups meeting the minimum peer-size requirement.

## Historical metadata snapshots
To remove the remaining universe and taxonomy look-ahead, each scheduled data refresh should preserve a dated copy of the complete scheme metadata before applying the active-fund filters. Historical evaluations should select schemes and classifications from the latest snapshot available on or before each formation date. Until enough dated snapshots exist (or a reliable historical scheme master is sourced), results must be labelled as subject to survivorship and taxonomy bias.
\n