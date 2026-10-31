import pandas as pd
from fundrank.scoring import build_rankings

def test_percentile_direction_and_composite():
    data = pd.DataFrame({
        "scheme_code":[1,2,3],"scheme_name":["A","B","C"],
        "category_sub":["Equity"]*3,"category_group_clean":["Equity Scheme"]*3,
        "return_1m":[.01,.02,.03],"return_3m":[.01,.02,.03],
        "return_6m":[.01,.02,.03],"return_12m":[.01,.02,.03],
        "volatility":[.03,.02,.01],"max_drawdown":[-.10,-.05,-.01],
        "sharpe_ratio":[.1,.2,.3],"sortino_ratio":[.1,.2,.3]})
    result = build_rankings(data).sort_values("scheme_code")
    assert result.iloc[2]["score_return_1m"] > result.iloc[0]["score_return_1m"]
    assert result.iloc[2]["score_volatility"] > result.iloc[0]["score_volatility"]
    assert result.iloc[2]["composite_conservative"] > result.iloc[0]["composite_conservative"]
    assert (result["coverage_conservative"] == 100).all()
