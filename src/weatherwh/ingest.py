"""Fetch hourly weather from Open-Meteo (free, no API key) and flatten to rows."""
from __future__ import annotations

import datetime as dt
import time

import requests

from .config import HOURLY_VARIABLES, City

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class IngestError(RuntimeError):
    pass


def fetch_city_hourly(city: City, past_days: int = 7, forecast_days: int = 1,
                      session=None, max_attempts: int = 3,
                      backoff_s: float = 2.0) -> list[dict]:
    """Return one flat dict per hour for a city.

    Open-Meteo occasionally drops connections (TLS handshake timeouts), so
    transient network errors are retried with backoff before giving up.
    Non-200 responses are not retried: they are the API answering.
    """
    http = session or requests.Session()
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "hourly": ",".join(HOURLY_VARIABLES),
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": city.timezone,
    }
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = http.get(FORECAST_URL, params=params, timeout=30)
            break
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_attempts:
                time.sleep(backoff_s * attempt)
    else:
        raise IngestError(
            f"Open-Meteo unreachable for {city.name} after {max_attempts} "
            f"attempts: {last_exc}") from last_exc
    if resp.status_code != 200:
        raise IngestError(f"Open-Meteo returned {resp.status_code} for {city.name}")
    return flatten_payload(city, resp.json(), ingested_at=dt.datetime.now(dt.timezone.utc))


def flatten_payload(city: City, payload: dict, ingested_at: dt.datetime) -> list[dict]:
    """Turn the Open-Meteo hourly block into typed row dicts. Pure and testable."""
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    rows: list[dict] = []
    for i, raw_time in enumerate(times):
        row = {
            "city": city.name,
            "hour": dt.datetime.strptime(raw_time, "%Y-%m-%dT%H:%M"),
            "ingested_at": ingested_at,
        }
        for var in HOURLY_VARIABLES:
            values = hourly.get(var) or []
            row[var] = values[i] if i < len(values) else None
        rows.append(row)
    return rows


def fetch_all(cities, fetch=None) -> tuple[list[dict], list[str]]:
    """Fetch every city, tolerating per-city failures. Returns (rows, failures):
    one unreachable city must not discard the others' fresh data. Failures are
    returned as messages so the caller can fail the quality gate; the failed
    city logs no successful fetch, so source-fetch freshness keeps flagging it
    once its last good fetch is too old."""
    fetch = fetch or fetch_city_hourly
    rows: list[dict] = []
    failures: list[str] = []
    for city in cities:
        try:
            rows.extend(fetch(city))
        except IngestError as exc:
            failures.append(f"fetch failed for {city.name}: {exc}")
    return rows, failures
