# Methodology and research decisions

## Universe
The current universe follows the notebook filters: active schemes, Direct plan, Growth option, Open Ended Schemes, and at least three years of history. The most recent metadata NAV date is used as the reference; hard-coded dates are avoided. Active status does not guarantee a fresh NAV, so stale NAV checks remain a required validation step.

## NAV validation
Missing identifiers, invalid dates, non-numeric NAV, and non-positive NAV rows are removed. Duplicate scheme/date rows retain the last source row. Only strongly evidenced persistent decimal-scale shifts or isolated one-day spikes are corrected. Every correction is exported to cleaning_audit.csv. Ambiguous anomalies remain untouched. Historical hard-coded correction dates from the notebook were not copied blindly because multiple notebook cells contain conflicting correction versions.

## Returns
Period returns compare the latest NAV with the last available NAV on or before the calendar reference date (1, 3, 6, or 12 months before the latest date). Missing history remains missing.

## Risk metrics
- Annualised volatility: sample standard deviation of daily NAV returns multiplied by sqrt(252).
- Maximum drawdown: minimum NAV / running peak - 1 over the available history.
- Sharpe: annualised arithmetic mean daily return less the annual risk-free rate, divided by annualised volatility. The notebook's final reconstruction used a zero risk-free rate; this is the default and can be configured.
- Sortino: annualised arithmetic mean return less the risk-free rate, divided by target-zero downside deviation. Downside deviation is sqrt(mean(min(daily return, 0)^2)) multiplied by sqrt(252). Positive days contribute zero to the mean-square denominator. This replaces the notebook's final standard deviation of clipped returns, which is not the standard target-zero downside deviation.

These are arithmetic annualisations, not geometric CAGR estimates.

## Peer scoring
Each metric is converted to a 0-100 percentile within a peer group. Higher returns, Sharpe, Sortino, and less-negative drawdown receive higher scores. Lower volatility receives a higher score. The implementation prefers category_sub as the peer group and falls back to category_group_clean. This is more granular than pooling all equity or all debt schemes. Peer-group sizes and taxonomy still require review.

## Composite ranking
The four profile weights are carried forward from the research notebook and each totals 100. Only valid metric scores contribute. The weighted score is divided by the sum of available weights. coverage_* reports the available original weight mass (0-100). If no metric score is valid, the composite and rank remain missing.

## Questionnaire
The ten answers are each between 0 and 10. The weighted score is normalised as 100 * sum(answer_i * weight_i) / (10 * sum(weights)). This corrects the notebook's interim division-by-two normalisation.

## Limitations
Percentiles depend on the selected universe; broad subcategories can still contain different strategies. NAV-only data does not capture every fee, tax, liquidity, or manager factor. Historical results do not predict future performance.
