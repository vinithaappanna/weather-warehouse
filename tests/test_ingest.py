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
