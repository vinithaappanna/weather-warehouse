"""Pipeline configuration: the cities we track and where the warehouse lives."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float
    timezone: str = "America/New_York"


CITIES = [
    City("Newark", 40.7357, -74.1724),
    City("New York", 40.7128, -74.0060),
    City("Chicago", 41.8781, -87.6298, timezone="America/Chicago"),
    City("San Francisco", 37.7749, -122.4194, timezone="America/Los_Angeles"),
]

HOURLY_VARIABLES = ("temperature_2m", "precipitation", "wind_speed_10m")
