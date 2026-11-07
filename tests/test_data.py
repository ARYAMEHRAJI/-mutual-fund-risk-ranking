import pandas as pd
import pytest
import requests

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


def test_get_retries_connection_error_then_succeeds(monkeypatch):
    client = TigzigClient(max_attempts=3, retry_backoff=2)
    calls = []
    sleeps = []
    response = requests.Response()
    response.status_code = 200
    response._content = b"ok"

    def fake_get(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise requests.ConnectionError("remote disconnected")
        return response

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("fundrank.data.time.sleep", sleeps.append)

    assert client._get("https://example.test").text == "ok"
    assert len(calls) == 2
    assert sleeps == [2]


def test_get_retries_transient_http_status_and_honors_retry_after(monkeypatch):
    client = TigzigClient(max_attempts=3, retry_backoff=2)
    calls = []
    sleeps = []
    response = requests.Response()
    response.status_code = 429
    response.headers["Retry-After"] = "7"
    response.url = "https://example.test"

    success = requests.Response()
    success.status_code = 200
    success._content = b"ok"

    def fake_get(*args, **kwargs):
        calls.append(1)
        return response if len(calls) == 1 else success

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("fundrank.data.time.sleep", sleeps.append)

    assert client._get("https://example.test").text == "ok"
    assert len(calls) == 2
    assert sleeps == [7]


def test_get_does_not_retry_permanent_http_error(monkeypatch):
    client = TigzigClient(max_attempts=4, retry_backoff=1)
    calls = []
    sleeps = []
    response = requests.Response()
    response.status_code = 400
    response.url = "https://example.test"

    def fake_get(*args, **kwargs):
        calls.append(1)
        return response

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("fundrank.data.time.sleep", sleeps.append)

    with pytest.raises(requests.HTTPError):
        client._get("https://example.test")
    assert len(calls) == 1
    assert sleeps == []
