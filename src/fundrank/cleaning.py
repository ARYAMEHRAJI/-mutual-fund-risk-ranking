"""NAV validation and conservative anomaly correction."""
import numpy as np
import pandas as pd


def validate_nav(nav, as_of_date=None):
    """Validate NAV rows and exclude observations dated after the India-local as-of date."""
    required = {"scheme_code", "date", "nav"}
    missing = required.difference(nav.columns)
    if missing:
        raise ValueError(f"NAV data is missing columns: {sorted(missing)}")
    data = nav.copy()
    data["scheme_code"] = pd.to_numeric(data["scheme_code"], errors="coerce")
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["nav"] = pd.to_numeric(data["nav"], errors="coerce")
    data = data.dropna(subset=["scheme_code", "date", "nav"])
    if as_of_date is None:
        as_of_date = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
    as_of_date = pd.Timestamp(as_of_date).normalize().tz_localize(None) if pd.Timestamp(as_of_date).tzinfo else pd.Timestamp(as_of_date).normalize()
    data = data.loc[data["date"] <= as_of_date].copy()
    data = data.loc[data["nav"] > 0].copy()
    data["scheme_code"] = data["scheme_code"].astype("int64")
    return data.sort_values(["scheme_code", "date"]).drop_duplicates(["scheme_code", "date"], keep="last").reset_index(drop=True)


def correct_scale_anomalies(nav, jump_threshold=0.50, persistence_tolerance=0.05):
    """Correct clear persistent powers-of-ten shifts or isolated one-day spikes.

    Every correction is recorded. Ambiguous observations are intentionally retained.
    """
    data = nav.copy().sort_values(["scheme_code", "date"]).reset_index(drop=True)
    data["nav_clean"] = data["nav"].astype(float)
    audit = []
    factors = np.array([0.001, 0.01, 0.1, 10.0, 100.0, 1000.0])
    for code, group in data.groupby("scheme_code", sort=False):
        idx = group.index.to_list()
        vals = data.loc[idx, "nav_clean"].to_numpy(dtype=float)
        if len(vals) < 3:
            continue
        i = 1
        while i < len(vals) - 1:
            prev_v, cur_v, next_v = vals[i - 1], vals[i], vals[i + 1]
            jump = cur_v / prev_v - 1
            if abs(jump) > jump_threshold:
                ratio = cur_v / prev_v
                factor = float(factors[np.argmin(np.abs(np.log(factors) - np.log(abs(ratio))))])
                persistent = abs(abs(ratio) / factor - 1) <= persistence_tolerance and abs(next_v / cur_v - 1) <= persistence_tolerance
                if persistent and ratio > 0:
                    vals[i:] = vals[i:] / factor
                    audit.append({"scheme_code": int(code), "date": data.loc[idx[i], "date"],
                                  "type": "persistent_scale_shift", "factor_applied": 1 / factor,
                                  "original_nav": cur_v, "corrected_nav": vals[i]})
                    i += 1
                    continue
                neighbor_move = next_v / prev_v - 1
                midpoint = float(np.sqrt(prev_v * next_v))
                if abs(neighbor_move) <= persistence_tolerance and abs(cur_v / midpoint - 1) > jump_threshold:
                    vals[i] = midpoint
                    audit.append({"scheme_code": int(code), "date": data.loc[idx[i], "date"],
                                  "type": "isolated_spike_interpolation", "factor_applied": np.nan,
                                  "original_nav": cur_v, "corrected_nav": midpoint})
            i += 1
        data.loc[idx, "nav_clean"] = vals
    return data, pd.DataFrame(audit, columns=["scheme_code", "date", "type", "factor_applied", "original_nav", "corrected_nav"])
