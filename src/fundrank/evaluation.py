"""Model evaluation and ranking robustness utilities."""
import numpy as np
import pandas as pd
from .config import MAX_NAV_STALENESS_DAYS, MIN_HISTORY_YEARS, PROFILE_WEIGHTS
from .scoring import MIN_PEER_GROUP_SIZE


def evaluate_rankings(ranked, top_n=10):
    """Compare profile rankings with a trailing 12-month-return baseline."""
    rows = []
    for group_name, group in ranked.groupby("ranking_group", dropna=False):
        for profile in PROFILE_WEIGHTS:
            composite_col = f"composite_{profile.lower()}"
            valid = group.dropna(subset=[composite_col, "return_12m"])
            if len(group) < MIN_PEER_GROUP_SIZE or len(valid) < MIN_PEER_GROUP_SIZE:
                rows.append({
                    "ranking_group": group_name, "profile": profile,
                    "funds_with_valid_scores": int(len(valid)),
                    "spearman_vs_12m_return": np.nan, "top_n": top_n,
                    "top_n_overlap_count": np.nan, "top_n_overlap_ratio": np.nan,
                    "evaluation_status": "insufficient_peers",
                })
                continue
            baseline = valid.nlargest(top_n, "return_12m")
            top = valid.nlargest(top_n, composite_col)
            overlap = len(set(top["scheme_code"]) & set(baseline["scheme_code"]))
            rows.append({
                "ranking_group": group_name, "profile": profile,
                "funds_with_valid_scores": int(len(valid)),
                "spearman_vs_12m_return": valid[composite_col].corr(
                    valid["return_12m"], method="spearman"
                ),
                "top_n": min(top_n, len(baseline)),
                "top_n_overlap_count": overlap,
                "top_n_overlap_ratio": overlap / len(baseline) if len(baseline) else np.nan,
                "evaluation_status": "evaluated",
            })
    return pd.DataFrame(rows)


def weight_sensitivity(
    ranked, profile="Moderate", perturbation=0.10, simulations=100, random_state=42
):
    """Estimate rank instability under small random perturbations of profile weights."""
    if profile not in PROFILE_WEIGHTS:
        raise ValueError(f"Unknown profile: {profile}")
    if not 0 <= perturbation < 1:
        raise ValueError("perturbation must be in [0, 1)")
    weights = PROFILE_WEIGHTS[profile]
    rng = np.random.default_rng(random_state)
    results = []
    for group_name, group in ranked.groupby("ranking_group", dropna=False):
        if len(group) < MIN_PEER_GROUP_SIZE:
            continue
        ranks = []
        for _ in range(simulations):
            perturbed = {
                metric: weight * rng.uniform(1 - perturbation, 1 + perturbation)
                for metric, weight in weights.items()
            }
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


def evaluate_out_of_sample(
    nav, metadata, as_of_date=None, horizon_months=12, windows=3,
    min_history_years=MIN_HISTORY_YEARS, top_n=10,
):
    """Evaluate formation-date rankings against returns earned after formation.

    Uses rolling annual formation dates. Current metadata is reused, so the
    result has survivorship and taxonomy look-ahead limitations.
    """
    from .metrics import calculate_fund_metrics
    from .scoring import build_rankings

    required = {"scheme_code", "date", "nav_clean"}
    missing = required.difference(nav.columns)
    if missing:
        raise ValueError(f"Clean NAV data is missing columns: {sorted(missing)}")
    if horizon_months < 1 or windows < 1:
        raise ValueError("horizon_months and windows must be positive")

    data = nav.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(["scheme_code", "date"])
    as_of = pd.Timestamp(as_of_date) if as_of_date is not None else data["date"].max()
    as_of = as_of.normalize()
    meta_cols = [
        col for col in [
            "scheme_code", "category_group_clean", "category_sub", "amc",
            "scheme_plan", "scheme_option",
        ] if col in metadata.columns
    ]
    meta = metadata[meta_cols].drop_duplicates("scheme_code")
    rows = []

    for window_index in range(1, windows + 1):
        formation = as_of - pd.DateOffset(months=horizon_months * window_index)
        evaluation_date = formation + pd.DateOffset(months=horizon_months)
        if evaluation_date > as_of:
            continue

        forward_returns = {}
        for code, group in data.groupby("scheme_code", sort=False):
            before = group.loc[group["date"] <= formation]
            through_end = group.loc[group["date"] <= evaluation_date]
            if before.empty or through_end.empty:
                continue
            base_row, end_row = before.iloc[-1], through_end.iloc[-1]
            if (
                (formation - base_row["date"]).days > MAX_NAV_STALENESS_DAYS
                or (evaluation_date - end_row["date"]).days > MAX_NAV_STALENESS_DAYS
                or end_row["date"] <= base_row["date"]
                or float(base_row["nav_clean"]) <= 0
            ):
                continue
            forward_returns[int(code)] = (
                float(end_row["nav_clean"]) / float(base_row["nav_clean"]) - 1
            )

        history = data.loc[data["date"] <= formation].copy()
        if history.empty or not forward_returns:
            continue
        metrics = calculate_fund_metrics(history)
        history_cutoff = formation - pd.DateOffset(years=min_history_years)
        metrics = metrics.loc[
            (pd.to_datetime(metrics["first_date"]) <= history_cutoff)
            & (pd.to_datetime(metrics["last_date"]) >= formation - pd.Timedelta(days=MAX_NAV_STALENESS_DAYS))
        ].copy()
        metrics["forward_return"] = metrics["scheme_code"].map(forward_returns)
        metrics = metrics.dropna(subset=["forward_return"])
        if metrics.empty:
            continue

        ranked = build_rankings(metrics.merge(meta, on="scheme_code", how="left"))
        for group_name, group in ranked.groupby("ranking_group", dropna=False):
            for profile in PROFILE_WEIGHTS:
                composite_col = f"composite_{profile.lower()}"
                valid = group.dropna(subset=[composite_col, "forward_return"])
                if len(valid) < MIN_PEER_GROUP_SIZE:
                    rows.append({
                        "formation_date": formation.date().isoformat(),
                        "evaluation_date": evaluation_date.date().isoformat(),
                        "horizon_months": horizon_months,
                        "ranking_group": group_name, "profile": profile,
                        "funds_evaluated": int(len(valid)),
                        "spearman_vs_forward_return": np.nan, "top_n": top_n,
                        "top_n_overlap_count": np.nan, "top_n_overlap_ratio": np.nan,
                        "evaluation_status": "insufficient_peers",
                    })
                    continue
                baseline = valid.nlargest(top_n, "forward_return")
                model_top = valid.nlargest(top_n, composite_col)
                overlap = len(set(model_top["scheme_code"]) & set(baseline["scheme_code"]))
                rows.append({
                    "formation_date": formation.date().isoformat(),
                    "evaluation_date": evaluation_date.date().isoformat(),
                    "horizon_months": horizon_months,
                    "ranking_group": group_name, "profile": profile,
                    "funds_evaluated": int(len(valid)),
                    "spearman_vs_forward_return": valid[composite_col].corr(
                        valid["forward_return"], method="spearman"
                    ),
                    "top_n": min(top_n, len(baseline)),
                    "top_n_overlap_count": overlap,
                    "top_n_overlap_ratio": overlap / len(baseline) if len(baseline) else np.nan,
                    "evaluation_status": "evaluated",
                })
    return pd.DataFrame(rows)
