# Project status

This repository is the clean implementation target for the research notebook. The first scaffold includes an API client, eligibility filters, NAV validation, auditable anomaly correction, return and risk metrics, percentile scoring, four profile-specific weighted rankings, weight coverage, questionnaire normalisation, a pipeline entry point, a Streamlit dashboard, unit tests, and methodology documentation.

Before relying on the rankings, run the pipeline against a current API response, review cleaning_audit.csv, verify metadata freshness, and run the full test suite. The notebook's conflicting hard-coded NAV correction dates have not been copied blindly.
