import datetime as dt

from weatherwh import dashboard, extremes, warehouse

T0 = dt.datetime(2026, 11, 1)


def load(con, spec):
    """spec: (city, day_offset, precip_per_hour, wind) one row per day-hour 0."""
    rows = [{"city": c, "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
             "temperature_2m": 10.0, "precipitation": p, "wind_speed_10m": w}
            for c, d, p, w in spec]
    warehouse.refresh(con, rows)


def test_severe_days_flags_rain_wind_or_both_and_orders_newest_first():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 12.0, 10.0), ("A", 1, 0.0, 70.0), ("B", 1, 15.0, 80.0), ("B", 2, 1.0, 5.0)])
    out = extremes.severe_days(con)
    assert [(a["city"], a["reasons"]) for a in out] == [
        ("A", "strong wind"), ("B", "heavy rain + strong wind"), ("A", "heavy rain")]
    assert out[0]["day"] > out[-1]["day"]
    con.close()


def test_thresholds_are_inclusive_and_configurable():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 10.0, 50.0)])
    assert len(extremes.severe_days(con)) == 1
    assert extremes.severe_days(con, rain_mm=11, wind_kmh=51) == []
    con.close()


def test_precip_by_city_counts_wet_days():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 2.0, 0.0), ("A", 1, 0.5, 0.0), ("B", 0, 5.0, 0.0)])
    assert extremes.precip_by_city(con) == [("B", 5.0, 1), ("A", 2.5, 1)]
    con.close()


def test_dashboard_sections_with_and_without_severe_days():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 0.0, 5.0)])
    md = dashboard.render_markdown(con)
    assert "## Severe-weather days" in md and "None in the current window." in md
    assert "## Precipitation" in md
    con.close()
