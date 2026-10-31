import pandas as pd
from fundrank.data import TigzigClient


def test_eligible_funds_excludes_future_metadata_dates():
    metadata = pd.DataFrame({
        "scheme_code": [1, 2, 3],
        "is_active": [True, True, True],
        "scheme_plan": ["Direct", "Direct", "Direct"],
        "scheme_option": ["Growth", "Growth", "Growth"],
        "scheme_type": ["Open Ended Schemes"] * 3,
        "first_date": ["2018-01-01"] * 3,
        "last_date": ["2024-01-10", "2024-01-11", "2024-01-08"],
    })
    eligible = TigzigClient().eligible_funds(metadata, as_of_date="2024-01-10")
    assert set(eligible["scheme_code"]) == {1, 3}
    assert eligible["last_date"].max() == pd.Timestamp("2024-01-10")
