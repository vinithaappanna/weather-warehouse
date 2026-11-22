import datetime as dt
import json

import pytest

from weatherwh import ingest
from weatherwh.config import City

NEWARK = City("Newark", 40.7357, -74.1724)

PAYLOAD = {
    "hourly": {
        "time": ["2026-11-14T00:00", "2026-11-14T01:00", "2026-11-14T02:00"],
        "temperature_2m": [8.1, 7.6, 7.2],
        "precipitation": [0.0, 0.0, 0.2],
        "wind_speed_10m": [11.0, 9.5, 8.8],
    }
}

INGESTED = dt.datetime(2026, 11, 15, 12, 0, tzinfo=dt.timezone.utc)


def test_flatten_payload_shapes_rows():
    rows = ingest.flatten_payload(NEWARK, PAYLOAD, INGESTED)
    assert len(rows) == 3
    first = rows[0]
    assert first["city"] == "Newark"
    assert first["hour"] == dt.datetime(2026, 11, 14, 0, 0)
    assert first["temperature_2m"] == 8.1
    assert first["ingested_at"] == INGESTED


def test_flatten_payload_tolerates_missing_variable():
    payload = {"hourly": {"time": ["2026-11-14T00:00"], "temperature_2m": [5.0]}}
    rows = ingest.flatten_payload(NEWARK, payload, INGESTED)
    assert rows[0]["precipitation"] is None
    assert rows[0]["wind_speed_10m"] is None


def test_flatten_payload_empty():
    assert ingest.flatten_payload(NEWARK, {}, INGESTED) == []


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.response


def test_fetch_city_hourly_sends_expected_params():
    session = FakeSession(FakeResponse(200, PAYLOAD))
    rows = ingest.fetch_city_hourly(NEWARK, session=session)
    params = session.calls[0][1]
    assert params["latitude"] == NEWARK.latitude
    assert "temperature_2m" in params["hourly"]
    assert params["timezone"] == "America/New_York"
    assert len(rows) == 3


def test_fetch_city_hourly_raises_on_error():
    session = FakeSession(FakeResponse(429, {}))
    with pytest.raises(ingest.IngestError):
        ingest.fetch_city_hourly(NEWARK, session=session)


class FlakySession:
    def __init__(self, fail_times, response):
        self.fail_times = fail_times
        self.response = response
        self.n = 0

    def get(self, url, params=None, timeout=None):
        self.n += 1
        if self.n <= self.fail_times:
            import requests
            raise requests.ConnectionError("handshake timeout")
        return self.response


def test_fetch_retries_transient_network_errors():
    session = FlakySession(2, FakeResponse(200, PAYLOAD))
    rows = ingest.fetch_city_hourly(NEWARK, session=session, backoff_s=0)
    assert session.n == 3 and len(rows) == 3


def test_fetch_gives_up_after_max_attempts():
    session = FlakySession(5, FakeResponse(200, PAYLOAD))
    with pytest.raises(ingest.IngestError):
        ingest.fetch_city_hourly(NEWARK, session=session, max_attempts=3, backoff_s=0)
    assert session.n == 3


def test_fetch_all_keeps_good_cities_and_reports_failures():
    from types import SimpleNamespace as NS
    from weatherwh.ingest import IngestError, fetch_all
    cities = [NS(name="A"), NS(name="B"), NS(name="C")]
    def fake(city):
        if city.name == "B":
            raise IngestError("Open-Meteo unreachable for B after 3 attempts: timeout")
        return [{"city": city.name, "hour": 1}]
    rows, failures = fetch_all(cities, fetch=fake)
    assert [r["city"] for r in rows] == ["A", "C"]
    assert len(failures) == 1 and failures[0].startswith("fetch failed for B")
    assert fetch_all([], fetch=fake) == ([], [])
    # non-ingest bugs are not swallowed
    import pytest
    with pytest.raises(KeyError):
        fetch_all(cities, fetch=lambda c: (_ for _ in ()).throw(KeyError("bug")))
