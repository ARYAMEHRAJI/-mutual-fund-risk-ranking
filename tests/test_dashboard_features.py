import pandas as pd

from fundrank.dashboard_features import (
    add_standalone_risk_score,
    equal_weight_portfolio,
    make_pdf_report,
)


def test_standalone_risk_score_is_between_zero_and_100():
    data = pd.DataFrame({
        "volatility": [0.1, 0.2, 0.3],
        "max_drawdown": [-0.05, -0.10, -0.20],
    })
    result = add_standalone_risk_score(data)
    assert result["risk_score"].between(0, 100).all()
    assert result["risk_score"].is_monotonic_increasing


def test_equal_weight_portfolio_selects_top_funds():
    data = pd.DataFrame({
        "scheme_code": [1, 2, 3, 4],
        "composite_growth": [20, 80, 60, 40],
    })
    result = equal_weight_portfolio(data, "composite_growth", count=2)
    assert result["scheme_code"].tolist() == [2, 3]
    assert result["portfolio_weight_pct"].tolist() == [50.0, 50.0]


def test_pdf_report_is_created():
    data = pd.DataFrame({
        "scheme_name": ["Fund A"],
        "scheme_code": [123],
        "rank_growth": [1],
        "composite_growth": [90.0],
        "return_12m": [0.15],
        "volatility": [0.08],
        "max_drawdown": [-0.04],
        "sharpe_ratio": [1.2],
        "sortino_ratio": [1.5],
    })
    pdf = make_pdf_report(data, "Growth", "2026-11-07")
    assert pdf.startswith(b"%PDF")
