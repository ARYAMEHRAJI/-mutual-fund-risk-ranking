# Data dictionary

## NAV input
- scheme_code: provider's scheme identifier
- scheme_name: scheme name
- date: NAV observation date
- nav: published NAV
- nav_clean: NAV after audited scale/spike correction

## Metrics
- return_1m / 3m / 6m / 12m: cumulative return over the stated calendar lookback
- volatility: annualised sample standard deviation of daily returns
- max_drawdown: worst peak-to-trough decline over available history
- sharpe_ratio: annualised excess arithmetic return divided by annualised volatility; unavailable when volatility is below the configured stability floor
- sortino_ratio: annualised excess arithmetic return divided by annualised target-zero downside deviation; unavailable when downside deviation is below the configured stability floor
- score_*: peer-group percentile score from 0 to 100; left missing for groups with fewer than five peers
- composite_*: weighted score for one investor profile
- coverage_*: sum of valid metric weights, from 0 to 100
- rank_*: rank within ranking_group, where 1 is best; missing for insufficient peer groups
- ranking_group: subcategory or fallback category label used for peer comparisons
- ranking_group_size: number of funds in the assigned peer group
- ranking_group_status: sufficient_peers or insufficient_peers

## Evaluation outputs
- ranking_evaluation.csv: in-sample diagnostic against trailing 12-month returns; not independent prediction validation
- out_of_sample_evaluation.csv: historical formation-date ranking compared with the following 12-month forward return
- weight_sensitivity.csv: rank variation under random small changes to profile weights
- cleaning_audit.csv: list of NAV corrections and their original/corrected values
- future_nav_excluded.csv: raw NAV rows dated after the pipeline's India-local as-of date

The output also carries scheme metadata when supplied by the API.
