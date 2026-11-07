"""Tigzig API ingestion helpers."""
import time
from email.utils import parsedate_to_datetime
from io import StringIO

import pandas as pd
import requests

from .config import (
    API_BASE_URL,
    API_BATCH_SIZE,
    API_REQUEST_DELAY,
    API_TIMEOUT,
    MIN_HISTORY_YEARS,
    MAX_NAV_STALENESS_DAYS,
)


class TigzigClient:
    def __init__(
        self,
        base_url=API_BASE_URL,
        timeout=API_TIMEOUT,
        max_attempts=4,
        retry_backoff=30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_attempts = max(1, int(max_attempts))
        self.retry_backoff = max(0, float(retry_backoff))
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "mutual-fund-risk-ranking/0.1"})

    @staticmethod
    def _retry_after_seconds(response):
        """Return a valid Retry-After delay, supporting seconds and HTTP dates."""
        value = response.headers.get("Retry-After") if response is not None else None
        if not value:
            return None
        try:
            return max(0, float(value))
        except (TypeError, ValueError):
            try:
                from datetime import datetime, timezone

                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return max(0, (retry_at - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None

    def _get(self, url, params=None):
        """GET with bounded retries for transient network and server failures."""
        for attempt in range(self.max_attempts):
            response = None
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response
            except (requests.ConnectionError, requests.Timeout):
                if attempt + 1 >= self.max_attempts:
                    raise
            except requests.HTTPError:
                status = response.status_code if response is not None else None
                if status != 429 and not (status is not None and 500 <= status < 600):
                    raise
                if attempt + 1 >= self.max_attempts:
                    raise

            retry_after = self._retry_after_seconds(response)
            delay = retry_after if retry_after is not None else self.retry_backoff * (2 ** attempt)
            time.sleep(delay)

        raise RuntimeError("Tigzig request exhausted retries unexpectedly")

    def latest_funds(self):
        response = self._get(f"{self.base_url}/download", {"format": "latest"})
        return pd.read_csv(StringIO(response.text))

    def eligible_funds(self, metadata=None, as_of_date=None):
        funds = self.latest_funds() if metadata is None else metadata.copy()
        required = {"scheme_code", "is_active", "scheme_plan", "scheme_option", "scheme_type", "first_date"}
        missing = required.difference(funds.columns)
        if missing:
            raise ValueError(f"Metadata is missing required columns: {sorted(missing)}")
        if as_of_date is None:
            as_of_date = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
        as_of_date = pd.Timestamp(as_of_date)
        as_of_date = as_of_date.tz_localize(None) if as_of_date.tzinfo else as_of_date
        as_of_date = as_of_date.normalize()
        active = funds["is_active"].astype(str).str.lower().isin({"true", "1", "yes"})
        mask = (active & funds["scheme_plan"].astype(str).str.casefold().eq("direct")
                & funds["scheme_option"].astype(str).str.casefold().eq("growth")
                & funds["scheme_type"].astype(str).str.casefold().eq("open ended schemes"))
        selected = funds.loc[mask].copy()
        selected["first_date"] = pd.to_datetime(selected["first_date"], errors="coerce")
        if "last_date" in selected:
            selected["last_date"] = pd.to_datetime(selected["last_date"], errors="coerce")
            # A metadata date later than today's India-local date is not a valid freshness anchor.
            selected = selected.loc[selected["last_date"] <= as_of_date].copy()
            if selected.empty:
                return selected.reset_index(drop=True)
            latest_valid_date = selected["last_date"].max()
            selected = selected.loc[selected["last_date"] >= latest_valid_date - pd.Timedelta(days=MAX_NAV_STALENESS_DAYS)].copy()
            as_of = latest_valid_date
        else:
            as_of = as_of_date
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
