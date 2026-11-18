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


def test_day_status_uses_city_local_boundary():
    # 2026-11-19 03:00 UTC is still Nov 18 in Chicago (21:00 CST) and San Francisco (19:00 PST)
    now = dt.datetime(2026, 11, 19, 3, 0, tzinfo=dt.timezone.utc)
    assert extremes.city_today("Chicago", now) == dt.date(2026, 11, 18)
    assert extremes.day_status("Chicago", dt.date(2026, 11, 18), now).startswith("in progress")
    assert extremes.day_status("Chicago", dt.date(2026, 11, 17), now) == "complete"
    # Newark is already past midnight? No: 22:00 EST, still Nov 18
    assert extremes.city_today("Newark", now) == dt.date(2026, 11, 18)
    assert extremes.city_today("Unknown City", now) == dt.date(2026, 11, 19)  # UTC fallback


def test_severe_days_carry_status_and_dashboard_labels_illustrative():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 12.0, 10.0)])
    row = extremes.severe_days(con)[0]
    assert row["status"] == "complete"  # 2026-11-01 is long past
    md = dashboard.render_markdown(con)
    assert "not official weather alerts" in md and "model output" in md
    con.close()


def test_reloading_refreshes_forecast_hours_without_new_rows():
    con = warehouse.connect(":memory:")
    base = dict(city="A", hour=T0, ingested_at=T0, temperature_2m=10.0,
                precipitation=5.0, wind_speed_10m=3.0)
    assert warehouse.load_raw(con, [base]) == 1
    later = dict(base, precipitation=0.2, ingested_at=T0 + dt.timedelta(hours=6))
    assert warehouse.load_raw(con, [later]) == 0  # not a new row...
    row = con.execute("SELECT precipitation, ingested_at FROM raw_weather_hourly").fetchall()
    assert row == [(0.2, T0 + dt.timedelta(hours=6))]  # ...but values refreshed
    assert warehouse.load_raw(con, [later]) == 0  # identical reload: still one row
    assert con.execute("SELECT count(*) FROM raw_weather_hourly").fetchall()[0][0] == 1
    con.close()
