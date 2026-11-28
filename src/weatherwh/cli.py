"""Read-only query CLI over the daily mart: city history, severe days, latest.

Day status is shown so in-progress days (which include forecast hours) are
never mistaken for completed observed totals. Thresholds are illustrative."""
from __future__ import annotations

import argparse

from . import extremes

COLS = "city, day, avg_temp_c, min_temp_c, max_temp_c, total_precip_mm, max_wind_kmh"


def city_history(con, city: str, days: int = 7) -> list[dict]:
    rows = con.execute(
        f"SELECT {COLS} FROM mart_daily_city WHERE lower(city) = lower(?) "
        "ORDER BY day DESC LIMIT ?", [city, days]).fetchall()
    keys = [c.strip() for c in COLS.split(",")]
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        d["status"] = extremes.day_status(d["city"], d["day"])
        out.append(d)
    return out


def latest_by_city(con) -> list[dict]:
    rows = con.execute(
        f"SELECT {COLS} FROM mart_daily_city m WHERE day = "
        "(SELECT max(day) FROM mart_daily_city x WHERE x.city = m.city) ORDER BY city").fetchall()
    keys = [c.strip() for c in COLS.split(",")]
    return [dict(zip(keys, r), status=extremes.day_status(r[0], r[1])) for r in rows]


def _fmt(rows: list[dict]) -> str:
    if not rows:
        return "no rows"
    return "\n".join(
        f"{r['city']:<14} {r['day']} avg {r['avg_temp_c']}C  "
        f"rain {r['total_precip_mm']} mm  wind {r['max_wind_kmh']} km/h  [{r['status']}]"
        for r in rows)


def main(argv=None, con=None) -> int:
    ap = argparse.ArgumentParser(prog="weather-query")
    ap.add_argument("--db", default="data/warehouse.duckdb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("city"); c.add_argument("name"); c.add_argument("--days", type=int, default=7)
    sub.add_parser("latest")
    sub.add_parser("severe")
    sub.add_parser("dry")
    args = ap.parse_args(argv)
    if con is None:
        import duckdb
        con = duckdb.connect(args.db, read_only=True)
    if args.cmd == "city":
        rows = city_history(con, args.name, args.days)
        print(_fmt(rows))
        return 0 if rows else 1
    if args.cmd == "latest":
        print(_fmt(latest_by_city(con)))
        return 0
    if args.cmd == "dry":
        runs = extremes.longest_dry_streaks(con)
        print("\n".join(f"{r['city']:<14} {r['days']} days ({r['start']} to {r['end']})" for r in runs)
              or "no complete dry days")
        print("Model output; dry means under 0.1 mm/day, an illustrative cutoff.")
        return 0
    sev = extremes.severe_days(con)
    print("\n".join(f"{s['city']:<14} {s['day']} {s['reasons']} (rain {s['precip_mm']} mm, "
                    f"wind {s['max_wind_kmh']} km/h) [{s['status']}]" for s in sev)
          or "no days over the illustrative thresholds")
    print("Illustrative thresholds, not official weather alerts.")
    return 0
