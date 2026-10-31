# Project status

The research implementation includes API ingestion, eligibility filters, NAV validation, auditable anomaly correction, risk/return metrics, four profile-specific weighted rankings, questionnaire normalisation, a Streamlit dashboard, unit tests, and methodology documentation.

Recent model-quality safeguards:
- Sharpe and Sortino are left unavailable when their annualised denominator is below the configurable 0.5% stability floor.
- Peer groups with fewer than five funds are not assigned percentile scores or ranks.
- The pipeline runs rolling 12-month out-of-sample evaluation at three historical formation dates.

The in-sample comparison with trailing 12-month return is only a consistency diagnostic because that return is also a model input. The new forward-return evaluation is more independent, but still has survivorship and taxonomy look-ahead limitations because the current fund universe and metadata are reused at historical dates.

After code changes, run the test workflow and refresh the data pipeline. Review cleaning_audit.csv, ranking_group_status, ranking_evaluation.csv, out_of_sample_evaluation.csv, and weight_sensitivity.csv before interpreting rankings.
