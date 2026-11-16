"""DuckDB warehouse: raw layer, staging model, and daily-summary mart."""
from __future__ import annotations

import duckdb

from .config import HOURLY_VARIABLES

RAW_TABLE = "raw_weather_hourly"


def connect(path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    return duckdb.connect(path)


def _run(con, sql: str, params=None) -> None:
    """Execute and fully consume the result: newer DuckDB errors if a
    connection has an unconsumed result when the next statement runs."""
    cur = con.execute(sql, params) if params else con.execute(sql)
    cur.fetchall()


def _scalar(con, sql: str, params=None):
    """Execute a single-value query, consuming every row it returns."""
    cur = con.execute(sql, params) if params else con.execute(sql)
    rows = cur.fetchall()
    return rows[0][0] if rows else None


def ensure_raw_table(con) -> None:
    _run(con,
        f"""
        CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
            city VARCHAR,
            hour TIMESTAMP,
            ingested_at TIMESTAMP,
            {", ".join(f"{v} DOUBLE" for v in HOURLY_VARIABLES)}
        )
        """
    )


def load_raw(con, rows: list[dict]) -> int:
    """Insert rows, skipping city/hour pairs already loaded (idempotent)."""
    ensure_raw_table(con)
    if not rows:
        return 0
    before = _scalar(con, f"SELECT count(*) FROM {RAW_TABLE}")
    import pandas as pd

    frame = pd.DataFrame(rows)
    con.register("_incoming", frame)
    cols = ", ".join(["city", "hour", "ingested_at", *HOURLY_VARIABLES])
    _run(con,
        f"""
        INSERT INTO {RAW_TABLE}
        SELECT {cols} FROM _incoming i
        WHERE NOT EXISTS (
            SELECT 1 FROM {RAW_TABLE} r
            WHERE r.city = i.city AND r.hour = i.hour
        )
        """
    )
    con.unregister("_incoming")
    after = _scalar(con, f"SELECT count(*) FROM {RAW_TABLE}")
    return after - before


def build_staging(con) -> None:
    """Typed, deduped, sanity-filtered view over raw."""
    _run(con,
        f"""
        CREATE OR REPLACE VIEW stg_hourly AS
        SELECT DISTINCT
            city,
            hour,
            CAST(temperature_2m AS DOUBLE) AS temperature_c,
            CAST(precipitation AS DOUBLE) AS precipitation_mm,
            CAST(wind_speed_10m AS DOUBLE) AS wind_kmh
        FROM {RAW_TABLE}
        WHERE hour IS NOT NULL
        """
    )


def build_marts(con) -> None:
    """Daily per-city summary."""
    _run(con,
        """
        CREATE OR REPLACE TABLE mart_daily_city AS
        SELECT
            city,
            CAST(hour AS DATE) AS day,
            round(avg(temperature_c), 2) AS avg_temp_c,
            round(min(temperature_c), 2) AS min_temp_c,
            round(max(temperature_c), 2) AS max_temp_c,
            round(sum(precipitation_mm), 2) AS total_precip_mm,
            round(max(wind_kmh), 2) AS max_wind_kmh,
            count(*) AS hours_observed
        FROM stg_hourly
        GROUP BY city, CAST(hour AS DATE)
        ORDER BY day, city
        """
    )


def refresh(con, rows: list[dict]) -> int:
    """Full daily refresh: load raw, rebuild staging and marts. Returns rows added."""
    added = load_raw(con, rows)
    build_staging(con)
    build_marts(con)
    return added


def export_mart_csv(con, path) -> int:
    """Snapshot mart_daily_city to CSV. The DuckDB file is gitignored, so this
    committed CSV is what lets daily history survive a fresh checkout.
    Returns rows written (excluding header)."""
    import csv as csv_mod

    cur = con.execute("SELECT * FROM mart_daily_city ORDER BY day, city")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv_mod.writer(fh)
        writer.writerow(cols)
        writer.writerows(rows)
    return len(rows)



def merge_mart_csv(con, path) -> int:
    """Merge historical city-day rows from a committed CSV snapshot into
    mart_daily_city. Freshly rebuilt rows win on overlap; rows older than the
    ingest window are restored, so the committed snapshot grows monotonically
    instead of shrinking to the API window after a fresh checkout.
    Returns rows merged."""
    import os

    path = str(path)
    if not os.path.exists(path):
        return 0
    safe = path.replace("'", "''")
    before = _scalar(con, "SELECT count(*) FROM mart_daily_city")
    _run(con,
        f"""
        CREATE OR REPLACE TEMP VIEW _mart_hist AS
        SELECT
            city::VARCHAR AS city,
            day::DATE AS day,
            avg_temp_c::DOUBLE AS avg_temp_c,
            min_temp_c::DOUBLE AS min_temp_c,
            max_temp_c::DOUBLE AS max_temp_c,
            total_precip_mm::DOUBLE AS total_precip_mm,
            max_wind_kmh::DOUBLE AS max_wind_kmh,
            hours_observed::BIGINT AS hours_observed
        FROM read_csv_auto('{safe}', header=true)
        """
    )
    _run(con,
        """
        INSERT INTO mart_daily_city
        SELECT h.* FROM _mart_hist h
        WHERE NOT EXISTS (
            SELECT 1 FROM mart_daily_city m
            WHERE m.city = h.city AND m.day = h.day
        )
        """
    )
    after = _scalar(con, "SELECT count(*) FROM mart_daily_city")
    return after - before
