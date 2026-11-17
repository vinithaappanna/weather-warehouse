"""Temperature anomaly detection over the daily mart.

Each city-day's average temperature is compared with that city's *other*
days (leave-one-out), so one extreme day cannot hide itself by inflating the
baseline. Informational only: anomalies are reported on the dashboard, they
do not fail the quality gate (a cold snap is weather, not bad data).
"""
from __future__ import annotations

import statistics


def find_anomalies(rows: list[tuple], threshold: float = 2.0,
                   min_days: int = 7) -> list[dict]:
    """rows: (city, day, avg_temp_c) tuples. Returns anomalies, largest |z| first.

    Cities with fewer than `min_days` days of history are skipped: a z-score
    over a handful of points is noise. A flat baseline (zero spread) cannot
    produce a z-score and is skipped too.
    """
    by_city: dict[str, list[tuple]] = {}
    for city, day, temp in rows:
        if temp is not None:
            by_city.setdefault(city, []).append((day, float(temp)))
    out = []
    for city, days in by_city.items():
        if len(days) < min_days:
            continue
        for i, (day, temp) in enumerate(days):
            others = [t for j, (_d, t) in enumerate(days) if j != i]
            spread = statistics.pstdev(others)
            if spread == 0:
                continue
            z = (temp - statistics.fmean(others)) / spread
            if abs(z) >= threshold:
                out.append({"city": city, "day": day, "avg_temp_c": temp, "z": round(z, 2)})
    return sorted(out, key=lambda a: (-abs(a["z"]), a["city"], str(a["day"])))


def load_and_find(con, **kwargs) -> list[dict]:
    rows = con.execute(
        "SELECT city, day, avg_temp_c FROM mart_daily_city ORDER BY city, day"
    ).fetchall()
    return find_anomalies(rows, **kwargs)
