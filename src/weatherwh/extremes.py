"""Severe-weather days from the daily mart: heavy rain and strong wind.

Thresholds are illustrative (not official warning criteria). Useful as a
disruption signal, e.g. days when claims-heavy facilities or travel are
likely affected. Informational only.
"""
from __future__ import annotations

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
                    "max_wind_kmh": wind, "reasons": " + ".join(reasons)})
    return out


def precip_by_city(con) -> list[tuple[str, float, int]]:
    """(city, total precipitation mm, wet days) over the mart, wettest first.
    A wet day has at least 1 mm."""
    return con.execute(
        "SELECT city, round(sum(total_precip_mm), 1), "
        "count(*) FILTER (WHERE total_precip_mm >= 1) "
        "FROM mart_daily_city GROUP BY city ORDER BY 2 DESC, city"
    ).fetchall()
