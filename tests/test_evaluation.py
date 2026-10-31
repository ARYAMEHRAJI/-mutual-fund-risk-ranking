import pandas as pd
from fundrank.evaluation import evaluate_rankings, weight_sensitivity

def sample_ranked():
    rows = []
    for i in range(1, 7):
        row = {"scheme_code": i, "ranking_group": "Equity", "return_12m": i / 100}
        for metric in ["return_1m", "return_3m", "return_6m", "return_12m", "volatility", "max_drawdown", "sharpe_ratio", "sortino_ratio"]:
            row[f"score_{metric}"] = i * 10
        rows.append(row)
    return pd.DataFrame(rows)

def test_evaluation_returns_profile_comparisons():
    ranked = sample_ranked()
    for profile in ["conservative", "moderate", "growth", "aggressive"]:
        ranked[f"composite_{profile}"] = ranked["return_12m"] * 100
    result = evaluate_rankings(ranked, top_n=3)
    assert len(result) == 4
    assert (result["top_n_overlap_ratio"] == 1).all()

def test_weight_sensitivity_is_reproducible():
    ranked = sample_ranked()
    a = weight_sensitivity(ranked, simulations=10, random_state=7)
    b = weight_sensitivity(ranked, simulations=10, random_state=7)
    assert a["mean_rank"].tolist() == b["mean_rank"].tolist()
