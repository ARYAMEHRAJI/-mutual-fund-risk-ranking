# Mutual Fund Risk & Return Ranking System

A research-oriented Python project for analysing mutual fund NAV histories, measuring risk and return, and ranking funds under investor risk profiles.

> Status: initial project scaffold. Methodology and implementation are being migrated and validated from the research notebook.

## Project goals

- Ingest mutual-fund metadata and historical NAV data from the Tigzig API (AMFI data republished by Tigzig).
- Validate, clean, and document NAV observations.
- Calculate period returns and risk metrics.
- Convert metrics to peer-group percentile scores.
- Build profile-specific composite rankings with transparent weight coverage.
- Evaluate ranking behaviour and expose results through a Streamlit dashboard.

## Research safeguards

- Missing metrics are not silently replaced with zero.
- Composite scores are renormalised over available metric weights, and coverage is reported.
- Peer groups must be sufficiently comparable; broad groups are provisional until taxonomy is validated.
- Sortino downside deviation uses a documented target-return convention.
- All results must record the latest available NAV date and data freshness.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python scripts/run_pipeline.py
streamlit run app/dashboard.py
```

## Project layout

```text
app/                 Streamlit dashboard
config/              Project and metric configuration
src/fundrank/        Reusable data and ranking package
scripts/             Pipeline entry points
tests/               Automated tests
docs/                Methodology and data documentation
notebooks/           Original research notebook (to be migrated)
```

## Data source

Tigzig Mutual Fund API: https://api.tigzig.com/mf/v1/docs

The API republishes Indian mutual-fund NAV data sourced from AMFI. Check the provider's current terms, limits, and availability before scheduled production use.

## Disclaimer

This software is for research and educational purposes. Rankings are quantitative outputs, not personalised investment advice or guarantees of future performance.
