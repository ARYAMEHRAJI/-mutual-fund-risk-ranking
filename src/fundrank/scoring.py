"""Peer-group percentile scoring and composite rankings."""
import numpy as np
import pandas as pd
from .config import METRIC_HIGHER_IS_BETTER, PROFILE_WEIGHTS

MIN_PEER_GROUP_SIZE = 5


def assign_ranking_group(data, min_peer_size=MIN_PEER_GROUP_SIZE):
    """Use a subcategory only when it has enough peers; otherwise use its parent group."""
    sub = data.get("category_sub", pd.Series(index=data.index, dtype="object")).astype("string").str.strip()
    fallback = data.get("category_group_clean", pd.Series("Unclassified", index=data.index)).astype("string")
    invalid = sub.isna() | sub.eq("") | sub.str.casefold().isin({"nan", "none", "unknown"})
    counts = sub[~invalid].value_counts()
    enough_peers = sub.map(counts).fillna(0).ge(min_peer_size)
    return sub.where((~invalid) & enough_peers, fallback).fillna("Unclassified").astype(str)


def add_percentile_scores(data, group_col="ranking_group", min_peer_size=MIN_PEER_GROUP_SIZE):
    result = data.copy()
    if group_col not in result:
        result[group_col] = assign_ranking_group(result)
    group_sizes = result.groupby(group_col, dropna=False)[group_col].transform("size")
    result["ranking_group_size"] = group_sizes.astype(int)
    result["ranking_group_status"] = np.where(
        group_sizes >= min_peer_size, "sufficient_peers", "insufficient_peers"
    )

    for metric, higher_better in METRIC_HIGHER_IS_BETTER.items():
        if metric not in result:
            raise ValueError(f"Missing metric column: {metric}")
        col = f"score_{metric}"
        result[col] = np.nan
        for _, indices in result.groupby(group_col, dropna=False).groups.items():
            if len(indices) < min_peer_size:
                continue
            vals = result.loc[indices, metric]
            valid = vals.notna()
            if valid.any():
                pct = vals.loc[valid].rank(method="average", pct=True, ascending=True)
                result.loc[pct.index, col] = (
                    pct * 100 if higher_better else (1 - pct) * 100
                )
    return result


def add_composite_rankings(data):
    result = data.copy()
    for profile, weights in PROFILE_WEIGHTS.items():
        weighted_sum = pd.Series(0.0, index=result.index)
        valid_weight = pd.Series(0.0, index=result.index)
        for metric, weight in weights.items():
            col = f"score_{metric}"
            if col not in result:
                raise ValueError(f"Missing percentile score column: {col}")
            valid = result[col].notna()
            weighted_sum.loc[valid] += result.loc[valid, col] * weight
            valid_weight.loc[valid] += weight
        result[f"coverage_{profile.lower()}"] = valid_weight
        result[f"composite_{profile.lower()}"] = weighted_sum.div(
            valid_weight.where(valid_weight > 0)
        )
        result[f"rank_{profile.lower()}"] = result.groupby("ranking_group")[
            f"composite_{profile.lower()}"
        ].rank(method="min", ascending=False)
    return result


def build_rankings(data):
    result = data.copy()
    result["ranking_group"] = assign_ranking_group(result)
    return add_composite_rankings(
        add_percentile_scores(result, min_peer_size=MIN_PEER_GROUP_SIZE)
    )
