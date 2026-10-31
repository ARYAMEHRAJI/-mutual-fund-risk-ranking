"""Model evaluation and ranking robustness utilities."""
import numpy as np
import pandas as pd
from .config import PROFILE_WEIGHTS

def evaluate_rankings(ranked, top_n=10):
    """Compare profile rankings with a return_12m-only baseline within each peer group."""
    rows = []
    for group_name, group in ranked.groupby("ranking_group", dropna=False):
        baseline = group.dropna(subset=["return_12m"]).nlargest(top_n, "return_12m")
        baseline_ids = set(baseline["scheme_code"].tolist())
        for profile in PROFILE_WEIGHTS:
            key = profile.lower()
            composite_col = f"composite_{key}"
            valid = group.dropna(subset=[composite_col, "return_12m"])
            top = valid.nlargest(top_n, composite_col)
            top_ids = set(top["scheme_code"].tolist())
            overlap = len(top_ids & baseline_ids)
            rows.append({
                "ranking_group": group_name,
                "profile": profile,
                "funds_with_valid_scores": int(valid.shape[0]),
                "spearman_vs_12m_return": valid[composite_col].corr(valid["return_12m"], method="spearman") if len(valid) > 1 else np.nan,
                "top_n": top_n,
                "top_n_overlap_count": overlap,
                "top_n_overlap_ratio": overlap / len(baseline_ids) if baseline_ids else np.nan,
            })
    return pd.DataFrame(rows)

def weight_sensitivity(ranked, profile="Moderate", perturbation=0.10, simulations=100, random_state=42):
    """Estimate rank instability under small random perturbations of profile weights."""
    if profile not in PROFILE_WEIGHTS:
        raise ValueError(f"Unknown profile: {profile}")
    if not 0 <= perturbation < 1:
        raise ValueError("perturbation must be in [0, 1)")
    weights = PROFILE_WEIGHTS[profile]
    rng = np.random.default_rng(random_state)
    results = []
    for group_name, group in ranked.groupby("ranking_group", dropna=False):
        ranks = []
        for _ in range(simulations):
            perturbed = {m: w * rng.uniform(1 - perturbation, 1 + perturbation) for m, w in weights.items()}
            numerator = pd.Series(0.0, index=group.index)
            denominator = pd.Series(0.0, index=group.index)
            for metric, weight in perturbed.items():
                col = f"score_{metric}"
                valid = group[col].notna()
                numerator.loc[valid] += group.loc[valid, col] * weight
                denominator.loc[valid] += weight
            score = numerator.div(denominator.where(denominator > 0))
            ranks.append(score.rank(method="average", ascending=False))
        rank_frame = pd.concat(ranks, axis=1)
        results.append(pd.DataFrame({
            "scheme_code": group["scheme_code"],
            "ranking_group": group_name,
            "profile": profile,
            "mean_rank": rank_frame.mean(axis=1),
            "rank_std": rank_frame.std(axis=1, ddof=0),
            "simulations": simulations,
        }, index=group.index))
    return pd.concat(results).reset_index(drop=True) if results else pd.DataFrame()
