import pandas as pd
from fundrank.scoring import build_rankings


def test_percentile_direction_and_composite():
    data = pd.DataFrame({
        "scheme_code": [1, 2, 3, 4, 5],
        "scheme_name": ["A", "B", "C", "D", "E"],
        "category_sub": ["Equity"] * 5,
        "category_group_clean": ["Equity Scheme"] * 5,
        "return_1m": [.01, .02, .03, .04, .05],
        "return_3m": [.01, .02, .03, .04, .05],
        "return_6m": [.01, .02, .03, .04, .05],
        "return_12m": [.01, .02, .03, .04, .05],
        "volatility": [.05, .04, .03, .02, .01],
        "max_drawdown": [-.10, -.08, -.05, -.03, -.01],
        "sharpe_ratio": [.1, .2, .3, .4, .5],
        "sortino_ratio": [.1, .2, .3, .4, .5],
    })
    result = build_rankings(data).sort_values("scheme_code")
    assert result.iloc[4]["score_return_1m"] > result.iloc[0]["score_return_1m"]
    assert result.iloc[4]["score_volatility"] > result.iloc[0]["score_volatility"]
    assert result.iloc[4]["composite_conservative"] > result.iloc[0]["composite_conservative"]
    assert (result["coverage_conservative"] == 100).all()
    assert (result["ranking_group_status"] == "sufficient_peers").all()


def test_groups_smaller_than_minimum_are_not_ranked():
    data = pd.DataFrame({
        "scheme_code": [1, 2, 3],
        "category_sub": ["Tiny"] * 3,
        "category_group_clean": ["Small Category"] * 3,
        "return_1m": [.01, .02, .03],
        "return_3m": [.01, .02, .03],
        "return_6m": [.01, .02, .03],
        "return_12m": [.01, .02, .03],
        "volatility": [.03, .02, .01],
        "max_drawdown": [-.1, -.05, -.01],
        "sharpe_ratio": [.1, .2, .3],
        "sortino_ratio": [.1, .2, .3],
    })
    result = build_rankings(data)
    assert result["ranking_group_size"].eq(3).all()
    assert result["ranking_group_status"].eq("insufficient_peers").all()
    assert result["composite_conservative"].isna().all()
    assert result["rank_conservative"].isna().all()
