"""Ten-question risk questionnaire scoring."""
from .config import RISK_PROFILE_BANDS, RISK_QUESTION_WEIGHTS

def score_risk_questionnaire(answers):
    if len(answers) != 10:
        raise ValueError("Exactly 10 answers are required.")
    if any(not 0 <= float(value) <= 10 for value in answers):
        raise ValueError("Each answer must be between 0 and 10.")
    total = sum(float(a) * w for a, w in zip(answers, RISK_QUESTION_WEIGHTS))
    score = total / (10 * sum(RISK_QUESTION_WEIGHTS)) * 100
    for lower, upper, profile in RISK_PROFILE_BANDS:
        if lower <= score < upper or (profile == "Aggressive" and score <= upper):
            return round(score, 2), profile
    return round(score, 2), "Aggressive"
