from fundrank.config import PROFILE_WEIGHTS

def test_all_profile_weights_sum_to_100():
    for profile, weights in PROFILE_WEIGHTS.items():
        assert sum(weights.values()) == 100, profile
