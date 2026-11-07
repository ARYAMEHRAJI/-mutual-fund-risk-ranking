import numpy as np
import pandas as pd
from fundrank.metrics import calculate_fund_metrics
from fundrank.benchmark import add_benchmark_metrics, daily_fund_returns


def test_metrics_include_period_extremes_and_return_to_risk():
    nav = pd.DataFrame({
        "scheme_code": [1] * 6,
        "date": pd.date_range("2024-01-01", periods=6, freq="B"),
        "nav_clean": [100, 102, 101, 104, 103, 106],
    })
    row = calculate_fund_metrics(nav, risk_free_rate=0.0).iloc[0]
    assert np.isclose(row["period_end_return"], 0.06)
    assert np.isclose(row["best_daily_return"], 3 / 101)
    assert np.isclose(row["worst_daily_return"], -1 / 102)
    assert np.isfinite(row["annualized_return_to_volatility"])
    assert np.isfinite(row["volatility"])
    assert np.isfinite(row["sortino_ratio"])
    assert row["max_drawdown"] < 0


def test_alpha_beta_calculated_from_aligned_benchmark_returns(tmp_path):
    dates = pd.bdate_range("2024-01-01", periods=90)
    benchmark_returns = np.tile([0.001, -0.0005, 0.0008], 30)
    fund_returns = 0.0002 + 1.4 * benchmark_returns
    benchmark_levels = 100 * np.cumprod(1 + benchmark_returns)
    fund_levels = 50 * np.cumprod(1 + fund_returns)
    nav = pd.DataFrame({"scheme_code": [1] * len(dates), "date": dates, "nav_clean": fund_levels})
    metrics = calculate_fund_metrics(nav)
    metrics.attrs["daily_returns"] = daily_fund_returns(nav)
    metadata = pd.DataFrame({
        "scheme_code": [1], "scheme_name": ["Example Nifty 500 Equity Fund"],
        "category_sub": ["Equity - Large Cap"], "category_group_clean": ["Equity"],
    })
    pd.DataFrame({
        "date": dates, "benchmark_id": "NIFTY_500_TRI", "index_value": benchmark_levels,
    }).to_csv(tmp_path / "index_levels.csv", index=False)
    result = add_benchmark_metrics(metrics, metadata, tmp_path / "index_levels.csv")
    row = result.iloc[0]
    assert row["benchmark_status"] == "ok"
    assert row["benchmark_observations"] == 89
    assert np.isclose(row["beta"], 1.4, atol=1e-8)
    assert np.isfinite(row["alpha"])


def test_alpha_beta_are_missing_without_benchmark_history(tmp_path):
    nav = pd.DataFrame({
        "scheme_code": [1, 1, 1],
        "date": pd.date_range("2024-01-01", periods=3),
        "nav_clean": [100, 101, 102],
    })
    metrics = calculate_fund_metrics(nav)
    metrics.attrs["daily_returns"] = daily_fund_returns(nav)
    metadata = pd.DataFrame({
        "scheme_code": [1], "scheme_name": ["Example Nifty 500 Equity Fund"],
        "category_sub": ["Equity"], "category_group_clean": ["Equity"],
    })
    result = add_benchmark_metrics(metrics, metadata, tmp_path / "missing.csv")
    assert pd.isna(result.loc[0, "alpha"])
    assert pd.isna(result.loc[0, "beta"])
    assert result.loc[0, "benchmark_status"] == "benchmark_history_missing"
