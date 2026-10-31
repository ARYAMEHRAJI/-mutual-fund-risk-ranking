# Mutual Fund Risk & Return Ranking System

A research-oriented Python project for analysing Indian mutual-fund NAV histories, measuring risk and return, and ranking funds under investor risk profiles.

## Current implementation

The repository now contains the reusable analysis package, a data pipeline, a Streamlit dashboard, model-evaluation utilities, methodology notes, and automated tests. The original Colab notebook remains the research record and should be exported into the notebooks folder before the project is submitted.

## Main capabilities

- Download scheme metadata and historical NAV data from the Tigzig API.
- Filter active Direct Growth open-ended schemes with at least three years of history and recent NAV data.
- Validate NAV observations and create an auditable anomaly-correction report.
- Calculate 1, 3, 6, and 12-month returns, annualised volatility, maximum drawdown, Sharpe, and Sortino.
- Convert metrics into peer-group percentile scores.
- Rank funds for Conservative, Moderate, Growth, and Aggressive profiles using the project's agreed weights.
- Report metric-weight coverage instead of silently replacing missing values.
- Compare composite rankings with a 12-month-return-only baseline and estimate weight sensitivity.
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
docs/                   Methodology, data dictionary, migration notes
notebooks/              Research notebook archive
scripts/                Pipeline entry points
src/fundrank/           Reusable ingestion, cleaning, metrics and ranking code
tests/                  Automated unit tests
.github/workflows/      Test and scheduled refresh workflows
```

## Data source

Tigzig Mutual Fund API documentation: https://api.tigzig.com/mf/v1/docs

The API republishes Indian mutual-fund NAV data sourced from AMFI. Review the provider's terms, rate limits, and availability before production use.

## Research safeguards

- Missing metrics remain missing; composite scores use only available metric weights and report coverage.
- The Sortino denominator uses target-zero downside RMS, not the standard deviation of clipped returns.
- NAV corrections are logged; ambiguous anomalies are not silently changed.
- Subcategory peer groups are used only when they contain at least five funds; otherwise the parent category is used.
- The default Sharpe risk-free rate is zero to match the final notebook reconstruction and is configurable.
- Rankings are relative to the selected universe and are not forecasts.

## Disclaimer

For research and educational use only. Quantitative rankings are not personalised investment advice or guarantees of future performance.
