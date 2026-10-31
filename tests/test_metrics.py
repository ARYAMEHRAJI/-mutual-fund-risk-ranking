import numpy as np
import pandas as pd
from fundrank.metrics import calculate_fund_metrics


def test_metrics_calculate_expected_values():
    nav = pd.DataFrame({
        "scheme_code": [1] * 6,
        "date": pd.date_range("2024-01-01", periods=6, freq="B"),
        "nav_clean": [100, 102, 101, 104, 103, 106],
    })
    row = calculate_fund_metrics(nav, risk_free_rate=0.0).iloc[0]
    assert np.isclose(row["total_return"], 0.06)
    assert np.isfinite(row["volatility"])
    assert np.isfinite(row["sortino_ratio"])
    assert row["max_drawdown"] < 0


def test_risk_adjusted_ratios_are_missing_below_denominator_floor():
    nav = pd.DataFrame({
        "scheme_code": [1] * 20,
        "date": pd.date_range("2024-01-01", periods=20, freq="B"),
        "nav_clean": 100 * (1 + np.tile([0.00001, 0.00002], 10)).cumprod(),
    })
    row = calculate_fund_metrics(
        nav, risk_free_rate=0.0, min_risk_denominator=0.005
    ).iloc[0]
    assert row["volatility"] < 0.005
    assert np.isnan(row["sharpe_ratio"])
