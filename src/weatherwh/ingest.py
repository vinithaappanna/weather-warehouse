"""Fetch hourly weather from Open-Meteo (free, no API key) and flatten to rows."""
from __future__ import annotations

import datetime as dt

import requests

from .config import HOURLY_VARIABLES, City

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class IngestError(RuntimeError):
    pass


def fetch_city_hourly(city: City, past_days: int = 7, forecast_days: int = 1,
                      session=None) -> list[dict]:
    """Return one flat dict per hour for a city."""
    http = session or requests.Session()
    resp = http.get(
        FORECAST_URL,
        params={
            "latitude": city.latitude,
            "longitude": city.longitude,
            "hourly": ",".join(HOURLY_VARIABLES),
            "past_days": past_days,
            "forecast_days": forecast_days,
            "timezone": city.timezone,
        },
        timeout=30,
    )
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
