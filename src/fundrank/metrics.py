"""Return and risk metric calculations."""
import numpy as np
import pandas as pd
from .config import (
    MIN_ANNUALIZED_RISK_DENOMINATOR,
    RISK_FREE_RATE,
    TRADING_DAYS,
)


def _nav_at_or_before(group, target):
    eligible = group.loc[group["date"] <= target, "nav_clean"]
    return float(eligible.iloc[-1]) if not eligible.empty else np.nan


def calculate_fund_metrics(
    nav,
    risk_free_rate=RISK_FREE_RATE,
    min_risk_denominator=MIN_ANNUALIZED_RISK_DENOMINATOR,
):
    required = {"scheme_code", "date", "nav_clean"}
    missing = required.difference(nav.columns)
    if missing:
        raise ValueError(f"Clean NAV data is missing columns: {sorted(missing)}")
    if min_risk_denominator < 0:
        raise ValueError("min_risk_denominator must be non-negative")

    data = nav.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(["scheme_code", "date"])
    as_of = data["date"].max()
    periods = {"1m": 1, "3m": 3, "6m": 6, "12m": 12}
    rows = []

    for code, group in data.groupby("scheme_code", sort=False):
        group = group.reset_index(drop=True)
        values = group["nav_clean"].astype(float)
        daily = values.pct_change().dropna()
        latest = float(values.iloc[-1])
        row = {
            "scheme_code": int(code),
            "scheme_name": group["scheme_name"].iloc[-1] if "scheme_name" in group else None,
            "first_date": group["date"].iloc[0],
            "last_date": group["date"].iloc[-1],
            "observations": int(len(group)),
            "total_return": latest / float(values.iloc[0]) - 1,
        }

        for label, months in periods.items():
            base = _nav_at_or_before(group, as_of - pd.DateOffset(months=months))
            row[f"return_{label}"] = (
                latest / base - 1 if np.isfinite(base) and base > 0 else np.nan
            )

        std = float(daily.std(ddof=1)) if len(daily) > 1 else np.nan
        annual_mean = float(daily.mean() * TRADING_DAYS) if len(daily) else np.nan
        annual_vol = std * np.sqrt(TRADING_DAYS) if np.isfinite(std) else np.nan
        row["volatility"] = annual_vol
        row["max_drawdown"] = float((values / values.cummax() - 1).min())

        # Do not report unstable ratios when the annualised denominator is
        # below the configured floor (default: 0.5%).
        row["sharpe_ratio"] = (
            (annual_mean - risk_free_rate) / annual_vol
            if np.isfinite(annual_vol) and annual_vol >= min_risk_denominator
            else np.nan
        )

        # Target-zero downside deviation: RMS of min(daily return, 0),
        # including zero contributions from positive days.
        downside = np.minimum(daily.to_numpy(dtype=float), 0.0)
        downside_dev = (
            float(np.sqrt(np.mean(np.square(downside)))) if len(downside) else np.nan
        )
        annual_downside = (
            downside_dev * np.sqrt(TRADING_DAYS)
            if np.isfinite(downside_dev)
            else np.nan
        )
        row["sortino_ratio"] = (
            (annual_mean - risk_free_rate) / annual_downside
            if np.isfinite(annual_downside)
            and annual_downside >= min_risk_denominator
            else np.nan
        )
        rows.append(row)

    result = pd.DataFrame(rows)
    result.attrs["as_of_date"] = as_of
    result.attrs["risk_free_rate"] = risk_free_rate
    result.attrs["min_risk_denominator"] = min_risk_denominator
    return result
