# Methodology and research decisions

## Universe
The current universe follows the notebook filters: active schemes, Direct plan, Growth option, Open Ended Schemes, and at least three years of history. The most recent metadata NAV date is used as the reference; hard-coded dates are avoided. Active status does not guarantee a fresh NAV, so stale NAV checks remain a required validation step.

## NAV validation
Missing identifiers, invalid dates, non-numeric NAV, and non-positive NAV rows are removed. Duplicate scheme/date rows retain the last source row. Only strongly evidenced persistent decimal-scale shifts or isolated one-day spikes are corrected. Every correction is exported to cleaning_audit.csv. Ambiguous anomalies remain untouched.

## Returns
Period returns compare the latest NAV with the last available NAV on or before the calendar reference date (1, 3, 6, or 12 months before the latest date). Missing history remains missing. Period-end return is the cumulative NAV return from the first to last available observation. Best and worst period returns are the maximum and minimum observed daily NAV returns.

## Risk metrics
- Annualised volatility: sample standard deviation of daily NAV returns multiplied by sqrt(252).
- Maximum drawdown: minimum NAV / running peak - 1 over the available history.
- Sharpe: annualised arithmetic mean daily return less the annual risk-free rate, divided by annualised volatility.
- Sortino: annualised arithmetic mean return less the risk-free rate, divided by target-zero downside deviation.
- Return-to-risk ratio: annualised arithmetic mean return divided by annualised volatility; unlike Sharpe, it does not subtract the risk-free rate.
- Stability guardrail: risk-adjusted ratios are not reported when their annualised denominator is below the configured 0.5% floor.

## India benchmark, alpha and beta
Benchmark mapping is strategy-aware and is stored in src/fundrank/benchmark.py. Recognisable Nifty index funds are mapped to the named underlying Nifty TRI. Sector funds are mapped to their matching sector TRI (for example, banking to Nifty Bank TRI, IT to Nifty IT TRI, pharma to Nifty Pharma TRI, auto to Nifty Auto TRI and metals to Nifty Metal TRI). Diversified equity categories use Nifty 500 TRI as a broad-market proxy. This proxy is not a claim that Nifty 500 is the scheme's contractual benchmark; where the scheme's disclosed benchmark is available, that mapping should take precedence.

Debt, hybrid, gold/commodity and ambiguous strategies are intentionally left unmapped until a suitable benchmark is identified. An equity index must not be forced onto a debt or gold fund. Benchmark observations are supplied in data/benchmarks/index_levels.csv with columns date, benchmark_id, index_value. Values should be official daily Total Return Index (TRI) levels, not price-only index levels. Supported IDs are listed in data/benchmarks/README.md. When no series exists, alpha and beta remain missing and benchmark_status explains why.

Beta is sample covariance(fund daily return, benchmark daily return) divided by sample variance(benchmark daily return). Jensen alpha is the annualised mean daily CAPM residual: mean(r_fund - r_f - beta * (r_benchmark - r_f)) * 252. At least 60 overlapping daily observations are required. The default risk-free rate remains configurable and is currently 0.0; it is a transparent research assumption, not a current Indian Treasury-bill yield. A future data refresh should supply a matched daily risk-free series for stronger inference.

NSE explains that TRI includes reinvested dividends and is the appropriate comparison basis for mutual funds. Historical TRI observations are available through the Nifty Indices historical reports, subject to the relevant data access and usage terms.

## Peer scoring
Each metric is converted to a 0-100 percentile within a peer group. Existing profile weights are unchanged; the newly added descriptive and benchmark metrics are not silently added to the composite score. The implementation prefers category_sub as the peer group and falls back to category_group_clean. A final group must contain at least five funds to receive percentile scores or ranks.

## Composite ranking
The four profile weights are carried forward from the research notebook and each totals 100. Only valid metric scores contribute. The weighted score is divided by the sum of available weights. coverage_* reports the available original weight mass (0-100).

## Evaluation
In-sample evaluation is a consistency diagnostic, not independent predictive validation. Rolling out-of-sample tests truncate NAV at each formation date. Historical universe and taxonomy still have survivorship and look-ahead limitations.

## Questionnaire
The ten answers are each between 0 and 10. The weighted score is normalised to 0-100.

## Limitations
NAV-only data does not capture every fee, tax, liquidity, or manager factor. Historical results do not predict future performance. Missing benchmark data is reported explicitly, never filled with fabricated or proxy values without labelling.
