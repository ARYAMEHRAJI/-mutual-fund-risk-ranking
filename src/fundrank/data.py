"""Tigzig API ingestion helpers."""
import time
from io import StringIO
import pandas as pd
import requests
from .config import API_BASE_URL, API_BATCH_SIZE, API_REQUEST_DELAY, API_TIMEOUT, MIN_HISTORY_YEARS, MAX_NAV_STALENESS_DAYS

class TigzigClient:
    def __init__(self, base_url=API_BASE_URL, timeout=API_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "mutual-fund-risk-ranking/0.1"})

    def _get(self, url, params=None):
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    def latest_funds(self):
        response = self._get(f"{self.base_url}/download", {"format": "latest"})
        return pd.read_csv(StringIO(response.text))

    def eligible_funds(self, metadata=None):
        funds = self.latest_funds() if metadata is None else metadata.copy()
        required = {"scheme_code", "is_active", "scheme_plan", "scheme_option", "scheme_type", "first_date"}
        missing = required.difference(funds.columns)
        if missing:
            raise ValueError(f"Metadata is missing required columns: {sorted(missing)}")
        active = funds["is_active"].astype(str).str.lower().isin({"true", "1", "yes"})
        mask = (active & funds["scheme_plan"].astype(str).str.casefold().eq("direct")
                & funds["scheme_option"].astype(str).str.casefold().eq("growth")
                & funds["scheme_type"].astype(str).str.casefold().eq("open ended schemes"))
        selected = funds.loc[mask].copy()
        selected["first_date"] = pd.to_datetime(selected["first_date"], errors="coerce")
        if "last_date" in selected:
            selected["last_date"] = pd.to_datetime(selected["last_date"], errors="coerce")
            as_of = selected["last_date"].max()
            # Exclude stale NAV histories rather than treating old prices as current.
            selected = selected.loc[selected["last_date"] >= as_of - pd.Timedelta(days=MAX_NAV_STALENESS_DAYS)].copy()
        else:
            as_of = pd.Timestamp.now().normalize()
        cutoff = as_of - pd.DateOffset(years=MIN_HISTORY_YEARS)
        return selected.loc[selected["first_date"].le(cutoff)].reset_index(drop=True)

    def nav_for_schemes(self, scheme_codes, batch_size=API_BATCH_SIZE, delay_seconds=API_REQUEST_DELAY):
        codes = list(dict.fromkeys(int(code) for code in scheme_codes))
        batches = [codes[i:i + batch_size] for i in range(0, len(codes), batch_size)]
        records = []
        for batch_no, batch in enumerate(batches, start=1):
            payload = self._get(f"{self.base_url}/nav", {"schemes": ",".join(map(str, batch))}).json()
            schemes = payload.get("schemes", [])
            if not schemes and "scheme_code" in payload:
                schemes = [payload]
            for scheme in schemes:
                for item in scheme.get("data", []):
                    records.append({"scheme_code": int(scheme["scheme_code"]),
                                    "scheme_name": scheme.get("scheme_name"),
                                    "date": item.get("date"), "nav": item.get("nav")})
            if batch_no < len(batches) and delay_seconds > 0:
                time.sleep(delay_seconds)
        return pd.DataFrame(records, columns=["scheme_code", "scheme_name", "date", "nav"])
