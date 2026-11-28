"""Severe-weather days from the daily mart: heavy rain and strong wind.

Thresholds are illustrative (not official warning criteria). Useful as a
disruption signal, e.g. days when claims-heavy facilities or travel are
likely affected. Informational only.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

HEAVY_RAIN_MM = 10.0
STRONG_WIND_KMH = 50.0


def severe_days(con, rain_mm: float = HEAVY_RAIN_MM, wind_kmh: float = STRONG_WIND_KMH) -> list[dict]:
    """City-days at or over either threshold, newest first, then city."""
    rows = con.execute(
        "SELECT city, day, total_precip_mm, max_wind_kmh FROM mart_daily_city "
        "WHERE total_precip_mm >= ? OR max_wind_kmh >= ? ORDER BY day DESC, city",
        [rain_mm, wind_kmh],
    ).fetchall()
    out = []
    for city, day, precip, wind in rows:
        reasons = []
        if precip is not None and precip >= rain_mm:
            reasons.append("heavy rain")
        if wind is not None and wind >= wind_kmh:
            reasons.append("strong wind")
        out.append({"city": city, "day": day, "precip_mm": precip,
                    "max_wind_kmh": wind, "reasons": " + ".join(reasons),
                    "status": day_status(city, day)})
    return out


def precip_by_city(con) -> list[tuple[str, float, int]]:
    """(city, total precipitation mm, wet days) over the mart, wettest first.
    A wet day has at least 1 mm."""
    return con.execute(
        "SELECT city, round(sum(total_precip_mm), 1), "
        "count(*) FILTER (WHERE total_precip_mm >= 1) "
        "FROM mart_daily_city GROUP BY city ORDER BY 2 DESC, city"
    ).fetchall()


def city_today(city: str, now_utc: dt.datetime | None = None) -> dt.date:
    """Today's date in the city's own timezone (the warehouse's day boundary)."""
    from .config import CITIES
    tz = next((c.timezone for c in CITIES if c.name == city), "UTC")
    now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
    return now_utc.astimezone(ZoneInfo(tz)).date()


def day_status(city: str, day, now_utc: dt.datetime | None = None) -> str:
    """'complete' for city-local days that have ended; otherwise the day is
    still in progress and its totals include forecast hours."""
    return "complete" if day < city_today(city, now_utc) else "in progress (includes forecast hours)"


DRY_DAY_MM = 0.1


def longest_dry_streaks(con, now_utc: dt.datetime | None = None) -> list[dict]:
    """Longest run of consecutive complete days under DRY_DAY_MM total
    precipitation, per city (model output; in-progress days are excluded and a
    missing day ends a run). Ties keep the earliest run. Sorted by length then
    city. The 0.1 mm cutoff is an illustrative choice, not a standard."""
    rows = con.execute("SELECT city, day, total_precip_mm FROM mart_daily_city ORDER BY city, day").fetchall()
    best: dict[str, dict] = {}
    cur: dict[str, dict] = {}
    for city, day, precip in rows:
        if day_status(city, day, now_utc) != "complete":
            continue
        run = cur.get(city)
        dry = precip is not None and precip < DRY_DAY_MM
        if dry and run and day == run["end"] + dt.timedelta(days=1):
            run["end"], run["days"] = day, run["days"] + 1
        elif dry:
            run = cur[city] = {"city": city, "start": day, "end": day, "days": 1}
        else:
            cur.pop(city, None)
            continue
        if city not in best or run["days"] > best[city]["days"]:
            best[city] = dict(run)
    return sorted(best.values(), key=lambda r: (-r["days"], r["city"]))
