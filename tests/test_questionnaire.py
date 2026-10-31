from fundrank.questionnaire import score_risk_questionnaire

def test_questionnaire_normalizes_to_100():
    score, profile = score_risk_questionnaire([10] * 10)
    assert score == 100
    assert profile == "Aggressive"

def test_questionnaire_example_normalization():
    score, _ = score_risk_questionnaire([7.5, 6, 7, 7, 7, 7, 5, 7, 7, 7])
    assert 68.0 < score < 68.2
