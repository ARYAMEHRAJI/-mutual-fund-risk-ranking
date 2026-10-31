import numpy as np
import pandas as pd
from fundrank.evaluation import (
    _build_formation_rankings,
    evaluate_out_of_sample,
    evaluate_rankings,
    weight_sensitivity,
)


def sample_ranked():
    rows = []
    for i in range(1, 7):
        row = {"scheme_code": i, "ranking_group": "Equity", "return_12m": i / 100}
        for metric in [
            "return_1m", "return_3m", "return_6m", "return_12m",
            "volatility", "max_drawdown", "sharpe_ratio", "sortino_ratio",
        ]:
            row[f"score_{metric}"] = i * 10
        rows.append(row)
    return pd.DataFrame(rows)


def test_evaluation_returns_profile_comparisons():
    ranked = sample_ranked()
    for profile in ["conservative", "moderate", "growth", "aggressive"]:
        ranked[f"composite_{profile}"] = ranked["return_12m"] * 100
    result = evaluate_rankings(ranked, top_n=3)
    assert len(result) == 4
    assert result["top_n_overlap_ratio"].between(0, 1).all()
    assert result["evaluation_status"].eq("evaluated").all()


def test_weight_sensitivity_is_reproducible():
    ranked = sample_ranked()
    a = weight_sensitivity(ranked, simulations=10, random_state=7)
    b = weight_sensitivity(ranked, simulations=10, random_state=7)
    assert a["mean_rank"].tolist() == b["mean_rank"].tolist()


def test_out_of_sample_evaluation_uses_forward_returns():
    dates = pd.bdate_range("2019-01-01", "2025-12-31")
    rows, metadata = [], []
    growth_rates = [0.0001, 0.00015, 0.0002, 0.00025, 0.0003]
    for code, growth in enumerate(growth_rates, start=1):
        values = 100 * (1 + growth) ** np.arange(len(dates))
        rows.extend(
            {"scheme_code": code, "date": date, "nav": value}
            for date, value in zip(dates, values)
        )
        metadata.append({
            "scheme_code": code, "category_sub": "Large Cap",
            "category_group_clean": "Equity Scheme", "amc": "Test AMC",
            "scheme_plan": "Direct", "scheme_option": "Growth",
        })
    result = evaluate_out_of_sample(
        pd.DataFrame(rows), pd.DataFrame(metadata),
        as_of_date="2025-12-31", horizon_months=12,
        windows=1, min_history_years=3, top_n=3,
    )
    assert not result.empty
    assert result["evaluation_status"].eq("evaluated").all()
    assert (result["funds_evaluated"] == 5).all()
    assert result["top_n_overlap_ratio"].between(0, 1).all()
    assert result["top_n_overlap_ratio"].notna().all()



def test_top_n_overlap_is_not_reported_when_top_n_includes_every_fund():
    ranked = sample_ranked()
    for profile in ["conservative", "moderate", "growth", "aggressive"]:
        ranked[f"composite_{profile}"] = ranked["return_12m"] * 100
    result = evaluate_rankings(ranked, top_n=6)
    assert result["evaluation_status"].eq("evaluated").all()
    assert result["top_n_overlap_ratio"].isna().all()
    assert result["top_n_overlap_count"].isna().all()


def test_formation_ranking_is_invariant_to_future_nav_anomalies():
    dates = pd.bdate_range("2019-01-01", "2024-01-05")
    formation = pd.Timestamp("2023-12-29")
    rows, metadata = [], []
    growth_rates = [0.0001, 0.00015, 0.0002, 0.00025, 0.0003]
    for code, growth in enumerate(growth_rates, start=1):
        values = 100 * (1 + growth) ** np.arange(len(dates))
        for date, value in zip(dates, values):
            if date <= formation:
                rows.append({"scheme_code": code, "date": date, "nav": value})
            elif date in dates[dates > formation][:2]:
                # A future persistent scale shift must not alter the
                # historical formation-date metrics or ranking.
                rows.append({
                    "scheme_code": code,
                    "date": date,
                    "nav": value * (100 if code == 1 else 1),
                })
        metadata.append({
            "scheme_code": code, "category_sub": "Large Cap",
            "category_group_clean": "Equity Scheme", "amc": "Test AMC",
            "scheme_plan": "Direct", "scheme_option": "Growth",
        })

    nav_with_future = pd.DataFrame(rows)
    nav_at_formation = nav_with_future.loc[
        nav_with_future["date"] <= formation
    ].copy()
    ranked_before, _ = _build_formation_rankings(
        nav_at_formation, pd.DataFrame(metadata), formation, 3
    )
    ranked_after, _ = _build_formation_rankings(
        nav_with_future, pd.DataFrame(metadata), formation, 3
    )
    columns = [
        "scheme_code", "ranking_group", "composite_conservative",
        "composite_moderate", "composite_growth", "composite_aggressive",
    ]
    pd.testing.assert_frame_equal(
        ranked_before[columns].reset_index(drop=True),
        ranked_after[columns].reset_index(drop=True),
    )
\n