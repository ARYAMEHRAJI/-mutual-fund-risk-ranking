"""End-to-end data pipeline."""
from pathlib import Path
from .cleaning import correct_scale_anomalies, validate_nav
from .data import TigzigClient
from .metrics import calculate_fund_metrics
from .scoring import build_rankings
from .evaluation import evaluate_rankings

def run_pipeline(output_dir="data/processed", refresh=True):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    client = TigzigClient()
    metadata = client.latest_funds()
    eligible = client.eligible_funds(metadata)
    if eligible.empty:
        raise RuntimeError("No funds matched the configured eligibility and freshness filters.")
    if refresh:
        nav = client.nav_for_schemes(eligible["scheme_code"].tolist())
        nav.to_parquet(output / "nav_raw.parquet", index=False)
    else:
        path = output / "nav_raw.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing cached NAV file: {path}")
        import pandas as pd
        nav = pd.read_parquet(path)
    nav = validate_nav(nav)
    cleaned, audit = correct_scale_anomalies(nav)
    audit.to_csv(output / "cleaning_audit.csv", index=False)
    cleaned.to_parquet(output / "nav_clean.parquet", index=False)
    metrics = calculate_fund_metrics(cleaned)
    meta_cols = [c for c in ["scheme_code", "category_group_clean", "category_sub", "amc", "scheme_plan", "scheme_option"] if c in eligible.columns]
    enriched = metrics.merge(eligible[meta_cols].drop_duplicates("scheme_code"), on="scheme_code", how="left")
    ranked = build_rankings(enriched)
    ranked.to_csv(output / "fund_rankings.csv", index=False)
    ranked.to_parquet(output / "fund_rankings.parquet", index=False)
    evaluation = evaluate_rankings(ranked)
    evaluation.to_csv(output / "ranking_evaluation.csv", index=False)
    return ranked
