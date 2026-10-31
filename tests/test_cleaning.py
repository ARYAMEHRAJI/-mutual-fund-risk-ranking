import pandas as pd
from fundrank.cleaning import validate_nav, correct_scale_anomalies

def test_validate_removes_invalid_and_duplicate_rows():
    raw = pd.DataFrame({"scheme_code":[1,1,1,1],"date":["2024-01-01","2024-01-02","2024-01-02","bad"],"nav":[10,11,12,5]})
    clean = validate_nav(raw)
    assert len(clean) == 2
    assert clean.iloc[-1]["nav"] == 12

def test_corrects_clear_persistent_scale_shift():
    raw = pd.DataFrame({"scheme_code":[1,1,1,1],"date":pd.date_range("2024-01-01",periods=4),"nav":[10.0,1000.0,1010.0,1020.0]})
    clean, audit = correct_scale_anomalies(raw)
    assert len(audit) == 1
    assert clean["nav_clean"].tolist() == [10.0,10.0,10.1,10.2]
