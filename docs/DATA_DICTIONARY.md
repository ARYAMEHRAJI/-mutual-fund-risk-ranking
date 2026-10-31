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
- sharpe_ratio: annualised excess arithmetic return divided by annualised volatility
- sortino_ratio: annualised excess arithmetic return divided by annualised target-zero downside deviation
- score_*: peer-group percentile score from 0 to 100
- composite_*: weighted score for one investor profile
- coverage_*: sum of valid metric weights, from 0 to 100
- rank_*: rank within ranking_group, where 1 is best

The output also carries scheme metadata when supplied by the API.
