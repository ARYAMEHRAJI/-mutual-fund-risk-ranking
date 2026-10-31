"""End-to-end data pipeline."""
from pathlib import Path
import pandas as pd
from .cleaning import correct_scale_anomalies, validate_nav
from .data import TigzigClient
from .metrics import calculate_fund_metrics
from .scoring import build_rankings
from .evaluation import evaluate_rankings, evaluate_out_of_sample, weight_sensitivity


def run_pipeline(output_dir="data/processed", refresh=True):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    # Use one consistent India-local calendar date for metadata and NAV validation.
    as_of_date = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
    client = TigzigClient()
    metadata = client.latest_funds()
    eligible = client.eligible_funds(metadata, as_of_date=as_of_date)
    if eligible.empty:
        raise RuntimeError("No funds matched the configured eligibility and freshness filters.")
    if refresh:
        nav = client.nav_for_schemes(eligible["scheme_code"].tolist())
        nav.to_parquet(output / "nav_raw.parquet", index=False)
    else:
        path = output / "nav_raw.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing cached NAV file: {path}")
        nav = pd.read_parquet(path)

    parsed_dates = pd.to_datetime(nav["date"], errors="coerce")
    future_mask = parsed_dates > as_of_date
    future_nav = nav.loc[future_mask].copy()
    future_nav.to_csv(output / "future_nav_excluded.csv", index=False)
    nav = validate_nav(nav, as_of_date=as_of_date)
    cleaned, audit = correct_scale_anomalies(nav)
    audit.to_csv(output / "cleaning_audit.csv", index=False)
    cleaned.to_parquet(output / "nav_clean.parquet", index=False)

    metrics = calculate_fund_metrics(cleaned)
    meta_cols = [
        col for col in [
            "scheme_code", "category_group_clean", "category_sub", "amc",
            "scheme_plan", "scheme_option",
        ] if col in eligible.columns
    ]
    eligible_meta = eligible[meta_cols].drop_duplicates("scheme_code")
    enriched = metrics.merge(eligible_meta, on="scheme_code", how="left")
    ranked = build_rankings(enriched)
    ranked.to_csv(output / "fund_rankings.csv", index=False)
    ranked.to_parquet(output / "fund_rankings.parquet", index=False)

    evaluation = evaluate_rankings(ranked)
    evaluation.to_csv(output / "ranking_evaluation.csv", index=False)
    sensitivity = [
        weight_sensitivity(ranked, profile=name, simulations=100)
        for name in ["Conservative", "Moderate", "Growth", "Aggressive"]
    ]
    pd.concat(sensitivity, ignore_index=True).to_csv(
        output / "weight_sensitivity.csv", index=False
    )

    out_of_sample = evaluate_out_of_sample(
        cleaned, eligible_meta, as_of_date=as_of_date,
        horizon_months=12, windows=3,
    )
    out_of_sample.to_csv(output / "out_of_sample_evaluation.csv", index=False)

    print(f"Excluded future-dated NAV rows: {len(future_nav):,}")
    print(f"Pipeline complete: {len(ranked):,} funds")
    print(f"Latest NAV date: {pd.to_datetime(cleaned['date']).max()}")
    print(
        "Out-of-sample evaluations: "
        f"{int((out_of_sample.get('evaluation_status', pd.Series(dtype=str)) == 'evaluated').sum()):,}"
    )
    return ranked
