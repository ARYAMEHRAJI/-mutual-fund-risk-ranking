"""Benchmark mapping and Jensen alpha / beta calculations.

Benchmark history is supplied as a CSV with columns:
date,benchmark_id,index_value. Use official daily Total Return Index (TRI)
levels wherever available. No price-index substitution is made silently.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from .config import RISK_FREE_RATE, TRADING_DAYS

MIN_BENCHMARK_OBSERVATIONS = 60

# Explicit mappings use category/name clues from the AMFI/Tigzig scheme master.
# Unmapped debt, hybrid, gold and other strategies remain unbenchmarked until
# an economically suitable India benchmark series is supplied and mapped.
SECTOR_BENCHMARKS = {
    "bank": ("NIFTY_BANK_TRI", "Nifty Bank TRI"),
    "banking": ("NIFTY_BANK_TRI", "Nifty Bank TRI"),
    "information technology": ("NIFTY_IT_TRI", "Nifty IT TRI"),
    "it fund": ("NIFTY_IT_TRI", "Nifty IT TRI"),
    "pharma": ("NIFTY_PHARMA_TRI", "Nifty Pharma TRI"),
    "pharmaceutical": ("NIFTY_PHARMA_TRI", "Nifty Pharma TRI"),
    "auto": ("NIFTY_AUTO_TRI", "Nifty Auto TRI"),
    "automobile": ("NIFTY_AUTO_TRI", "Nifty Auto TRI"),
    "metal": ("NIFTY_METAL_TRI", "Nifty Metal TRI"),
    "financial services": ("NIFTY_FINANCIAL_SERVICES_TRI", "Nifty Financial Services TRI"),
    "realty": ("NIFTY_REALTY_TRI", "Nifty Realty TRI"),
    "fmcg": ("NIFTY_FMCG_TRI", "Nifty FMCG TRI"),
    "media": ("NIFTY_MEDIA_TRI", "Nifty Media TRI"),
    "energy": ("NIFTY_ENERGY_TRI", "Nifty Energy TRI"),
    "healthcare": ("NIFTY_HEALTHCARE_TRI", "Nifty Healthcare TRI"),
}


def resolve_benchmark(row):
    name = str(row.get("scheme_name") or "").casefold()
    category = str(row.get("category_sub") or "").casefold()
    group = str(row.get("category_group_clean") or "").casefold()
    text = " ".join((name, category, group))

    # Index funds should track their disclosed underlying index when its name
    # is recognisable; broad equity funds use a broad-market TRI proxy.
    if "nifty 500" in name or "nifty total market" in name:
        return "NIFTY_500_TRI", "Nifty 500 TRI"
    if "nifty next 50" in name:
        return "NIFTY_NEXT_50_TRI", "Nifty Next 50 TRI"
    if "nifty midcap 150" in name:
        return "NIFTY_MIDCAP_150_TRI", "Nifty Midcap 150 TRI"
    if "nifty smallcap 250" in name:
        return "NIFTY_SMALLCAP_250_TRI", "Nifty Smallcap 250 TRI"
    if "nifty 50" in name:
        return "NIFTY_50_TRI", "Nifty 50 TRI"

    for clue, benchmark in SECTOR_BENCHMARKS.items():
        if clue in text:
            return benchmark

    if "leverag" in name or "index" in name:
        return "NIFTY_50_TRI", "Nifty 50 TRI"
    if any(term in text for term in ("equity", "large cap", "mid cap", "small cap", "flexi cap",
                                      "multi cap", "focused", "value", "contra", "large & mid")):
        return "NIFTY_500_TRI", "Nifty 500 TRI"
    # Avoid forcing an equity index onto debt, hybrid, commodity or gold funds.
    return None, None


def add_benchmark_metrics(metrics, metadata, nav_returns=None,
                          levels_path="data/benchmarks/index_levels.csv",
                          risk_free_rate=RISK_FREE_RATE):
    meta_cols = [c for c in ("scheme_code", "scheme_name", "category_sub", "category_group_clean")
                 if c in metadata.columns]
    meta = metadata[meta_cols].drop_duplicates("scheme_code").copy()
    mapping = meta.apply(resolve_benchmark, axis=1, result_type="expand")
    mapping.columns = ["benchmark_id", "benchmark_name"]
    meta = pd.concat([meta.reset_index(drop=True), mapping.reset_index(drop=True)], axis=1)
    result = metrics.merge(meta[["scheme_code", "benchmark_id", "benchmark_name"]],
                           on="scheme_code", how="left")
    result["alpha"] = np.nan
    result["beta"] = np.nan
    result["benchmark_observations"] = 0
    result["benchmark_status"] = "unmapped_category"

    path = Path(levels_path)
    if not path.exists():
        result.loc[result["benchmark_id"].notna(), "benchmark_status"] = "benchmark_history_missing"
        return result

    levels = pd.read_csv(path)
    required = {"date", "benchmark_id", "index_value"}
    missing = required.difference(levels.columns)
    if missing:
        raise ValueError(f"Benchmark CSV is missing columns: {sorted(missing)}")
    levels["date"] = pd.to_datetime(levels["date"], errors="coerce")
    levels["index_value"] = pd.to_numeric(levels["index_value"], errors="coerce")
    levels = levels.dropna(subset=["date", "benchmark_id", "index_value"])
    levels = levels.loc[levels["index_value"] > 0].sort_values(["benchmark_id", "date"])
    levels["benchmark_return"] = levels.groupby("benchmark_id")["index_value"].pct_change()

    # Daily fund returns are supplied separately to avoid storing a DataFrame
    # inside pandas attrs (which can break equality checks during merge).
    if nav_returns is None:
        result.loc[result["benchmark_id"].notna(), "benchmark_status"] = "benchmark_history_loaded_fund_returns_unavailable"
        return result

    for _, row in result.iterrows():
        benchmark_id = row.get("benchmark_id")
        if not benchmark_id:
            continue
        benchmark = levels.loc[levels["benchmark_id"].eq(benchmark_id), ["date", "benchmark_return"]]
        if benchmark.empty:
            result.loc[result["scheme_code"].eq(row["scheme_code"]), "benchmark_status"] = "benchmark_series_missing"
            continue
        fund = nav_returns.loc[nav_returns["scheme_code"].eq(row["scheme_code"]), ["date", "fund_return"]]
        paired = fund.merge(benchmark, on="date", how="inner").dropna()
        if len(paired) < MIN_BENCHMARK_OBSERVATIONS:
            result.loc[result["scheme_code"].eq(row["scheme_code"]), "benchmark_status"] = "insufficient_overlap"
            result.loc[result["scheme_code"].eq(row["scheme_code"]), "benchmark_observations"] = len(paired)
            continue
        x = paired["benchmark_return"].to_numpy(dtype=float)
        y = paired["fund_return"].to_numpy(dtype=float)
        variance = float(np.var(x, ddof=1))
        if not np.isfinite(variance) or variance <= 0:
            result.loc[result["scheme_code"].eq(row["scheme_code"]), "benchmark_status"] = "invalid_benchmark_variance"
            continue
        beta = float(np.cov(y, x, ddof=1)[0, 1] / variance)
        rf_daily = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
        alpha = float((np.mean(y - rf_daily - beta * (x - rf_daily))) * TRADING_DAYS)
        mask = result["scheme_code"].eq(row["scheme_code"])
        result.loc[mask, "beta"] = beta
        result.loc[mask, "alpha"] = alpha
        result.loc[mask, "benchmark_observations"] = len(paired)
        result.loc[mask, "benchmark_status"] = "ok"
    return result


def daily_fund_returns(nav):
    data = nav.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["nav_clean"] = pd.to_numeric(data["nav_clean"], errors="coerce")
    data = data.dropna(subset=["date", "nav_clean"]).sort_values(["scheme_code", "date"])
    data["fund_return"] = data.groupby("scheme_code")["nav_clean"].pct_change()
    return data[["scheme_code", "date", "fund_return"]].dropna()
