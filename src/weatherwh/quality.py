"""Data quality checks over the warehouse. Each check returns a list of issues;
an empty list means the check passed."""
from __future__ import annotations

import datetime as dt


def check_no_null_temperatures(con) -> list[str]:
    n = con.execute(
        "SELECT count(*) FROM stg_hourly WHERE temperature_c IS NULL"
    ).fetchall()[0][0]
    return [f"{n} hourly rows have NULL temperature"] if n else []


def check_temperature_sane(con, low=-60.0, high=60.0) -> list[str]:
    rows = con.execute(
        "SELECT city, hour, temperature_c FROM stg_hourly "
        "WHERE temperature_c < ? OR temperature_c > ?",
        [low, high],
    ).fetchall()
    return [f"implausible temperature {t}C in {c} at {h}" for c, h, t in rows]


def check_precip_wind_sane(con, max_hourly_precip_mm=150.0, max_wind_kmh=250.0) -> list[str]:
    """Rain and wind must be non-negative and physically plausible per hour.
    NULLs are skipped (a missing value is not an implausible one); limits are
    generous sanity bounds, not weather thresholds."""
    rows = con.execute(
        "SELECT city, hour, precipitation_mm, wind_kmh FROM stg_hourly "
        "WHERE precipitation_mm < 0 OR precipitation_mm > ? OR wind_kmh < 0 OR wind_kmh > ? "
        "ORDER BY city, hour",
        [max_hourly_precip_mm, max_wind_kmh],
    ).fetchall()
    return [f"implausible precipitation {p} mm / wind {w} km/h in {c} at {h}" for c, h, p, w in rows]


def check_no_far_future_hours(con, now: dt.datetime | None = None,
                              horizon_hours: int = 24) -> list[str]:
    """Forecast rows legitimately cover the rest of today, so only flag rows
    beyond the forecast horizon (and any timezone slop)."""
    now = now or dt.datetime.now()
    cutoff = now + dt.timedelta(hours=horizon_hours)
    n = con.execute(
        "SELECT count(*) FROM stg_hourly WHERE hour > ?", [cutoff]
    ).fetchall()[0][0]
    return [f"{n} hourly rows are beyond the {horizon_hours}h forecast horizon"] if n else []


def check_full_days(con, expected_hours: int = 20) -> list[str]:
    """Flag city-days with suspiciously few observed hours."""
    rows = con.execute(
        "SELECT city, day, hours_observed FROM mart_daily_city "
        "WHERE hours_observed < ?",
        [expected_hours],
    ).fetchall()
    return [f"only {h} hours observed for {c} on {d}" for c, d, h in rows]


def check_all_cities_present(con, expected: list[str] | None = None) -> list[str]:
    """Every configured city must have rows in staging; a silently missing
    city would make dashboards look complete while dropping a source."""
    if expected is None:
        from .config import CITIES
        expected = [c.name for c in CITIES]
    present = {r[0] for r in con.execute("SELECT DISTINCT city FROM stg_hourly").fetchall()}
    return [f"no data for city {name}" for name in expected if name not in present]


def check_fresh_ingest(con, now: dt.datetime | None = None, max_age_hours: int = 6) -> list[str]:
    """The newest ingest must be recent, otherwise the daily job is serving
    stale data without anyone noticing."""
    now = now or dt.datetime.now()
    latest = con.execute("SELECT max(ingested_at) FROM raw_weather_hourly").fetchall()[0][0]
    if latest is None:
        return ["no ingest timestamps recorded"]
    age = (now - latest).total_seconds() / 3600
    return [f"latest ingest is {age:.1f}h old (limit {max_age_hours}h)"] if age > max_age_hours else []


def check_fresh_fetch(con, now: dt.datetime | None = None, max_age_hours: int = 6,
                      expected: list[str] | None = None) -> list[str]:
    """Source-fetch freshness: every city needs a recent fetch that returned
    rows. Uses fetch_log, not raw ingested_at, so an empty or failed fetch
    is detected even though cached rows still sit in the warehouse."""
    if expected is None:
        from .config import CITIES
        expected = [c.name for c in CITIES]
    now = now or dt.datetime.now()
    try:
        logged = con.execute(
            "SELECT city, max(fetched_at) FROM fetch_log WHERE rows_returned > 0 GROUP BY city"
        ).fetchall()
    except Exception:
        return ["no fetch log recorded"]
    last = dict(logged)
    issues = []
    for city in expected:
        if city not in last:
            issues.append(f"no successful fetch recorded for {city}")
        else:
            age = (now - last[city]).total_seconds() / 3600
            if age > max_age_hours:
                issues.append(f"last successful fetch for {city} is {age:.1f}h old (limit {max_age_hours}h)")
    return issues


def latest_available_hour(con) -> dict[str, dt.datetime]:
    """Latest weather hour held per city. Reported separately from fetch
    freshness: forecast_days=1 means this is normally later than 'now'."""
    return dict(con.execute("SELECT city, max(hour) FROM stg_hourly GROUP BY city").fetchall())


def run_all(con) -> list[str]:
    issues: list[str] = []
    for check in (check_no_null_temperatures, check_temperature_sane, check_precip_wind_sane,
                  check_no_far_future_hours, check_full_days):
        issues.extend(check(con))
    return issues
