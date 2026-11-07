# Methodology and research decisions

## Universe
The current universe follows the notebook filters: active schemes, Direct plan, Growth option, Open Ended Schemes, and at least three years of history. The most recent metadata NAV date is used as the reference; hard-coded dates are avoided. Active status does not guarantee a fresh NAV, so stale NAV checks remain a required validation step.

## NAV validation
Missing identifiers, invalid dates, non-numeric NAV, and non-positive NAV rows are removed. Duplicate scheme/date rows retain the last source row. Only strongly evidenced persistent decimal-scale shifts or isolated one-day spikes are corrected. Every correction is exported to cleaning_audit.csv. Ambiguous anomalies remain untouched.

## Returns
Period returns compare the latest NAV with the last available NAV on or before the calendar reference date (1, 3, 6, or 12 months before the latest date). Missing history remains missing. Cumulative total return is stored once as `total_return` (latest NAV divided by first NAV minus one). Best and worst returns are the maximum and minimum observed daily NAV returns.

## Risk metrics
- Annualised volatility: sample standard deviation of daily NAV returns multiplied by sqrt(252).
- Maximum drawdown: minimum NAV / running peak - 1 over the available history.
- Sharpe: annualised arithmetic mean daily return less the annual risk-free rate, divided by annualised volatility.
- Sortino: annualised arithmetic mean return less the risk-free rate, divided by target-zero downside deviation.
- Return-to-risk ratio: annualised arithmetic mean return divided by annualised volatility; unlike Sharpe, it does not subtract the risk-free rate.
- Stability guardrail: risk-adjusted ratios are not reported when their annualised denominator is below the configured 0.5% floor.

## Benchmark-relative metrics
Alpha and beta are not calculated in this version. The project does not currently include reliable, aligned daily total-return benchmark history covering the different fund strategies. These metrics are intentionally omitted rather than left blank or estimated against an unsuitable index. A future implementation should use each scheme’s disclosed benchmark where available and aligned official TRI observations.

## Peer scoring
Each metric is converted to a 0-100 percentile within a peer group. Existing profile weights are unchanged; descriptive metrics are not silently added to the composite score. The implementation prefers category_sub as the peer group and falls back to category_group_clean. A final group must contain at least five funds to receive percentile scores or ranks.

## Composite ranking
The four profile weights are carried forward from the research notebook and each totals 100. Only valid metric scores contribute. The weighted score is divided by the sum of available weights. coverage_* reports the available original weight mass (0-100).

## Evaluation
In-sample evaluation is a consistency diagnostic, not independent predictive validation. Rolling out-of-sample tests truncate NAV at each formation date. Historical universe and taxonomy still have survivorship and look-ahead limitations.

## Questionnaire
The ten answers are each between 0 and 10. The weighted score is normalised to 0-100.

## Limitations
NAV-only data does not capture every fee, tax, liquidity, or manager factor. Historical results do not predict future performance. Benchmark-relative alpha and beta are not part of the current metric set because suitable benchmark history is not yet available.
