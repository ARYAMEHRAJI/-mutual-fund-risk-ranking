"""Model evaluation and ranking robustness utilities."""
import numpy as np
import pandas as pd
from .config import MAX_NAV_STALENESS_DAYS, MIN_HISTORY_YEARS, PROFILE_WEIGHTS
from .scoring import MIN_PEER_GROUP_SIZE, build_rankings
from .cleaning import correct_scale_anomalies


def _spearman_corr(left, right):
    """Compute Spearman correlation without requiring SciPy."""
    pair = pd.concat([left, right], axis=1).dropna()
    if len(pair) < 2:
        return np.nan
    left_ranks = pair.iloc[:, 0].rank(method="average")
    right_ranks = pair.iloc[:, 1].rank(method="average")
    return left_ranks.corr(right_ranks, method="pearson")


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
            overlap_count = np.nan
            overlap_ratio = np.nan
            if len(valid) > top_n:
                baseline = valid.nlargest(top_n, "return_12m")
                top = valid.nlargest(top_n, composite_col)
                overlap_count = len(set(top["scheme_code"]) & set(baseline["scheme_code"]))
                overlap_ratio = overlap_count / len(baseline) if len(baseline) else np.nan
            rows.append({
                "ranking_group": group_name, "profile": profile,
                "funds_with_valid_scores": int(len(valid)),
                "spearman_vs_12m_return": _spearman_corr(valid[composite_col], valid["return_12m"]),
                "top_n": min(top_n, len(valid)),
                "top_n_overlap_count": overlap_count,
                "top_n_overlap_ratio": overlap_ratio,
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


def _build_formation_rankings(nav, metadata, formation_date, min_history_years):
    """Build rankings using only raw NAV observations available by formation_date."""
    from .metrics import calculate_fund_metrics

    history_raw = nav.loc[nav["date"] <= formation_date].copy()
    if history_raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Crucially, anomaly detection sees no observations after the formation date.
    history_clean, _ = correct_scale_anomalies(history_raw)
    metrics = calculate_fund_metrics(history_clean)
    history_cutoff = formation_date - pd.DateOffset(years=min_history_years)
    metrics = metrics.loc[
        (pd.to_datetime(metrics["first_date"]) <= history_cutoff)
        & (
            pd.to_datetime(metrics["last_date"])
            >= formation_date - pd.Timedelta(days=MAX_NAV_STALENESS_DAYS)
        )
    ].copy()
    if metrics.empty:
        return pd.DataFrame(), history_clean

    meta_cols = [
        col for col in [
            "scheme_code", "category_group_clean", "category_sub", "amc",
            "scheme_plan", "scheme_option",
        ] if col in metadata.columns
    ]
    if "scheme_code" not in meta_cols:
        raise ValueError("Metadata is missing required column: scheme_code")
    meta = metadata[meta_cols].drop_duplicates("scheme_code")
    ranked = build_rankings(metrics.merge(meta, on="scheme_code", how="left"))
    return ranked, history_clean


def evaluate_out_of_sample(
    nav, metadata, as_of_date=None, horizon_months=12, windows=3,
    min_history_years=MIN_HISTORY_YEARS, top_n=10,
):
    """Evaluate formation-date rankings against returns earned after formation.

    Feature cleaning and ranking are point-in-time: each formation only sees raw
    NAV observations dated on or before that formation. Forward-period NAV is
    cleaned separately through the evaluation date solely to measure outcomes.
    Current metadata is reused, so survivorship and taxonomy look-ahead remain.
    """
    required = {"scheme_code", "date", "nav"}
    missing = required.difference(nav.columns)
    if missing:
        raise ValueError(f"Raw NAV data is missing columns: {sorted(missing)}")
    if horizon_months < 1 or windows < 1:
        raise ValueError("horizon_months and windows must be positive")
    if "scheme_code" not in metadata.columns:
        raise ValueError("Metadata is missing required column: scheme_code")

    data = nav.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["scheme_code"] = pd.to_numeric(data["scheme_code"], errors="coerce")
    data["nav"] = pd.to_numeric(data["nav"], errors="coerce")
    data = data.dropna(subset=["scheme_code", "date", "nav"])
    data = data.loc[data["nav"] > 0].copy()
    data["scheme_code"] = data["scheme_code"].astype("int64")
    data = data.sort_values(["scheme_code", "date"])
    as_of = pd.Timestamp(as_of_date) if as_of_date is not None else data["date"].max()
    as_of = as_of.normalize()

    rows = []
    for window_index in range(1, windows + 1):
        formation = as_of - pd.DateOffset(months=horizon_months * window_index)
        evaluation_date = formation + pd.DateOffset(months=horizon_months)
        if evaluation_date > as_of:
            continue

        ranked, formation_clean = _build_formation_rankings(
            data, metadata, formation, min_history_years
        )
        if ranked.empty:
            continue

        # Use the formation-time cleaned NAV as the investable starting value.
        # Clean each target series only through its evaluation date; those
        # observations are outcomes, never inputs to the formation ranking.
        forward_returns = {}
        for code, group in data.groupby("scheme_code", sort=False):
            base_group = formation_clean.loc[
                formation_clean["scheme_code"].eq(code)
                & (formation_clean["date"] <= formation)
            ]
            target_raw = group.loc[group["date"] <= evaluation_date].copy()
            if base_group.empty or target_raw.empty:
                continue
            target_clean, _ = correct_scale_anomalies(target_raw)
            base_row = base_group.iloc[-1]
            end_row = target_clean.iloc[-1]
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

        ranked["forward_return"] = ranked["scheme_code"].map(forward_returns)
        ranked = ranked.dropna(subset=["forward_return"])
        if ranked.empty:
            continue

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
                overlap_count = np.nan
                overlap_ratio = np.nan
                if len(valid) > top_n:
                    baseline = valid.nlargest(top_n, "forward_return")
                    model_top = valid.nlargest(top_n, composite_col)
                    overlap_count = len(set(model_top["scheme_code"]) & set(baseline["scheme_code"]))
                    overlap_ratio = overlap_count / len(baseline) if len(baseline) else np.nan
                rows.append({
                    "formation_date": formation.date().isoformat(),
                    "evaluation_date": evaluation_date.date().isoformat(),
                    "horizon_months": horizon_months,
                    "ranking_group": group_name, "profile": profile,
                    "funds_evaluated": int(len(valid)),
                    "spearman_vs_forward_return": _spearman_corr(valid[composite_col], valid["forward_return"]),
                    "top_n": min(top_n, len(valid)),
                    "top_n_overlap_count": overlap_count,
                    "top_n_overlap_ratio": overlap_ratio,
                    "evaluation_status": "evaluated",
                })
    return pd.DataFrame(rows)
