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


def run_all(con) -> list[str]:
    issues: list[str] = []
    for check in (check_no_null_temperatures, check_temperature_sane,
                  check_no_far_future_hours, check_full_days):
        issues.extend(check(con))
    return issues
