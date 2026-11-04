# Mutual Fund Risk & Return Ranking System

A research-oriented Python project for analysing Indian mutual-fund NAV histories, measuring risk and return, and ranking funds under investor risk profiles.

## Main capabilities

- Download scheme metadata and historical NAV data from the Tigzig API.
- Archive the complete provider scheme metadata before applying active-fund and eligibility filters, creating a dated point-in-time universe for future evaluations.
- Filter active Direct Growth open-ended schemes with at least three years of history and recent NAV data.
- Validate NAV observations and create an auditable anomaly-correction report.
- Calculate 1, 3, 6, and 12-month returns, annualised volatility, maximum drawdown, Sharpe, and Sortino.
- Suppress risk-adjusted ratios when their annualised denominator is below a configurable stability floor.
- Convert metrics into peer-group percentile scores; groups with fewer than five funds are retained but not assigned relative ranks.
- Rank funds for Conservative, Moderate, Growth, and Aggressive profiles using the project's agreed weights.
- Report metric-weight coverage instead of silently replacing missing values.
- Compare composite rankings with an in-sample trailing-return diagnostic and run rolling 12-month forward-return evaluation.
- Estimate ranking sensitivity to small weight changes.
- Explore rankings in a Streamlit dashboard and export filtered results.

## Quick start

Install Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python scripts/run_pipeline.py
streamlit run app/dashboard.py
```

The first data refresh can take several minutes. The default request delay is 21 seconds between NAV batches to respect the provider's published request-rate limit. Adjust settings in .env only after checking the provider's current API policy.

## Repository layout

```text
app/                    Streamlit dashboard
data/raw/               Raw input cache (not committed)
data/processed/         Cleaned NAV and ranking outputs (not committed)
metadata_snapshots/     Dated full scheme metadata snapshots
docs/                   Methodology, data dictionary, migration notes
notebooks/              Research notebook archive
scripts/                Pipeline entry points
src/fundrank/           Reusable ingestion, cleaning, metrics and ranking code
tests/                  Unit tests
.github/workflows/      Tests and scheduled refresh
```

## Metadata snapshots and evaluation limits

Each successful pipeline run saves the complete metadata response to `metadata_snapshots/YYYY-MM-DD.json` before eligibility filters are applied. The scheduled GitHub Actions workflow commits this snapshot to the repository. This starts a historical record from the first successful run after this feature is merged; it does not recreate missing historical metadata from earlier years. Future out-of-sample evaluations can use these snapshots to reduce survivorship and category/taxonomy look-ahead bias.

## Data source

Tigzig Mutual Fund API documentation: https://api.tigzig.com/mf/v1/docs

The API republishes Indian mutual-fund NAV data sourced from AMFI. Review the provider's terms, rate limits, and availability before production use.

## Research safeguards

- Missing metrics remain missing; composite scores use only available metric weights and report coverage.
- Sharpe and Sortino use a configurable 0.5% annualised denominator floor to avoid unstable ratios near zero.
- The Sortino denominator uses target-zero downside RMS, not the standard deviation of clipped returns.
- NAV corrections are logged; ambiguous anomalies are not silently changed.
- Subcategory peer groups are used only when they contain at least five funds; parent groups smaller than five are not ranked.
- The default Sharpe risk-free rate is zero to match the final notebook reconstruction and is configurable.
- Out-of-sample evaluation uses only historical NAVs available at each formation date and measures the following 12-month return. Until dated metadata snapshots are used to reconstruct the historical eligible universe, older evaluations still contain survivorship and taxonomy look-ahead bias.
- Rankings are relative to the selected universe and are not forecasts.

## Disclaimer

For research and educational use only. Quantitative rankings are not personalised investment advice or guarantees of future performance.
