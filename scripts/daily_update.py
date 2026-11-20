#!/usr/bin/env python3
"""Daily refresh: ingest the last 7 days of hourly weather for every city,
load the warehouse (idempotently), rebuild marts, run quality checks, and
regenerate the dashboard. Exits non-zero if a quality check fails."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from weatherwh import config, dashboard, ingest, quality, warehouse

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "warehouse.duckdb"
REPORTS = ROOT / "reports"


def main() -> int:
    rows = []
    for city in config.CITIES:
        city_rows = ingest.fetch_city_hourly(city)
        print(f"{city.name}: fetched {len(city_rows)} hourly rows")
        rows.extend(city_rows)

    (ROOT / "data").mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)

    con = warehouse.connect(str(DB_PATH))
    warehouse.record_fetch(con, rows, [c.name for c in config.CITIES])
    added = warehouse.refresh(con, rows)
    print(f"warehouse: {added} new rows loaded")

    # Freshness is evaluated right after this run's own ingest, so the overnight
    # gap between rounds (3pm to 7am) cannot trip it: each run loads new hours stamped
    # now. It fails only if a run loads nothing new for over 6h (a stalled upstream).
    issues = (quality.run_all(con) + quality.check_all_cities_present(con)
              + quality.check_fresh_fetch(con))
    for city, hr in sorted(quality.latest_available_hour(con).items()):
        print(f"latest available hour {city}: {hr}")
    for issue in issues:
        print(f"QUALITY ISSUE: {issue}")

    # The DuckDB file is gitignored; the committed CSV is the durable store.
    # Merge its history back into the mart first (so the snapshot grows
    # monotonically across fresh checkouts), then re-export.
    csv_path = ROOT / "data" / "mart_daily_city.csv"
    merged = warehouse.merge_mart_csv(con, csv_path)
    if merged:
        print(f"restored {merged} historical city-days from CSV snapshot")
    written = warehouse.export_mart_csv(con, csv_path)
    print(f"exported {written} mart rows to data/mart_daily_city.csv")

    (REPORTS / "dashboard.md").write_text(dashboard.render_markdown(con), encoding="utf-8")
    if dashboard.plot_avg_temp(con, REPORTS / "avg_temp_by_city.png"):
        print("wrote chart")
    if dashboard.plot_precip(con, REPORTS / "precip_by_city.png"):
        print("wrote precip chart")
    if dashboard.plot_wind(con, REPORTS / "wind_by_city.png"):
        print("wrote wind chart")
    print("wrote reports/dashboard.md")
    con.close()
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
