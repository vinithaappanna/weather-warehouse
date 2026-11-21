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


def _row(city, hour, precip=0.0):
    return dict(city=city, hour=hour, ingested_at=hour, temperature_2m=10.0,
                precipitation=precip, wind_speed_10m=3.0)


def test_empty_fetch_fails_freshness_even_with_cached_rows():
    from weatherwh import quality
    con = warehouse.connect(":memory:")
    now = dt.datetime(2026, 11, 18, 12, 0)
    good = [_row("A", T0)]
    warehouse.record_fetch(con, good, ["A"], now=now - dt.timedelta(hours=10))
    warehouse.refresh(con, good)  # cached rows exist
    # a later run fetches nothing (empty payload): rows stay cached, fetch is logged as empty
    warehouse.record_fetch(con, [], ["A"], now=now)
    issues = quality.check_fresh_fetch(con, now=now, expected=["A"])
    assert issues and "10.0h old" in issues[0]
    # a genuine non-empty fetch clears it
    warehouse.record_fetch(con, good, ["A"], now=now)
    assert quality.check_fresh_fetch(con, now=now, expected=["A"]) == []
    con.close()


def test_missing_city_fetch_flagged_and_latest_hour_is_separate():
    from weatherwh import quality
    con = warehouse.connect(":memory:")
    now = dt.datetime(2026, 11, 18, 12, 0)
    rows = [_row("A", T0), _row("A", T0 + dt.timedelta(hours=30))]
    warehouse.record_fetch(con, rows, ["A", "B"], now=now)
    warehouse.refresh(con, rows)
    assert quality.check_fresh_fetch(con, now=now, expected=["A", "B"]) == [
        "no successful fetch recorded for B"]
    # latest available hour (forecast horizon) is independent of fetch time
    assert quality.latest_available_hour(con)["A"] == T0 + dt.timedelta(hours=30)
    con.close()


def test_revised_hour_flows_to_every_mart_and_dashboard():
    con = warehouse.connect(":memory:")
    first = [_row("A", T0, 40.0)]
    warehouse.refresh(con, first)
    assert "A" in dashboard.render_markdown(con) and extremes.severe_days(con)
    revised = [dict(_row("A", T0, 1.0), ingested_at=T0 + dt.timedelta(hours=6))]
    warehouse.refresh(con, revised)
    assert con.execute("SELECT total_precip_mm FROM mart_daily_city").fetchall() == [(1.0,)]
    assert extremes.severe_days(con) == []
    assert "40" not in "".join(l for l in dashboard.render_markdown(con).splitlines() if "| A |" in l)
    con.close()


def test_plot_precip_renders_and_handles_empty(tmp_path):
    con = warehouse.connect(":memory:")
    assert dashboard.plot_precip(_empty(), tmp_path / "e.png") is False
    load(con, [("A", 1, 3.0, 5.0), ("A", 2, 0.0, 5.0), ("B", 2, 12.0, 5.0)])
    now = dt.datetime(2026, 11, 2, 15, tzinfo=dt.timezone.utc)   # Nov 2 in progress
    assert dashboard.plot_precip(con, tmp_path / "p.png", now_utc=now) is True
    assert (tmp_path / "p.png").stat().st_size > 1000
    con.close()


def _empty():
    con = warehouse.connect(":memory:")
    warehouse.refresh(con, [])
    return con


def test_plot_wind_renders_with_threshold_and_embeds_in_dashboard(tmp_path):
    con = warehouse.connect(":memory:")
    assert dashboard.plot_wind(_empty(), tmp_path / "e.png") is False
    load(con, [("A", 1, 0.0, 20.0), ("A", 2, 0.0, 70.0), ("B", 2, 0.0, 10.0)])
    now = dt.datetime(2026, 11, 2, 15, tzinfo=dt.timezone.utc)
    assert dashboard.plot_wind(con, tmp_path / "w.png", now_utc=now) is True
    assert (tmp_path / "w.png").stat().st_size > 1000
    assert "wind_by_city.png" in dashboard.render_markdown(con)
    con.close()


def test_plot_temp_range_renders_and_embeds(tmp_path):
    con = warehouse.connect(":memory:")
    assert dashboard.plot_temp_range(_empty(), tmp_path / "e.png") is False
    load(con, [("A", 1, 0.0, 20.0), ("A", 2, 0.0, 70.0), ("B", 2, 0.0, 10.0)])
    now = dt.datetime(2026, 11, 2, 15, tzinfo=dt.timezone.utc)
    assert dashboard.plot_temp_range(con, tmp_path / "t.png", now_utc=now) is True
    assert (tmp_path / "t.png").stat().st_size > 1000
    assert "temp_range_by_city.png" in dashboard.render_markdown(con)
    con.close()


def test_daily_leaders_uses_latest_day_complete_everywhere():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 1.0, 20.0), ("B", 0, 5.0, 10.0), ("A", 1, 0.0, 99.0), ("B", 1, 0.0, 99.0)])
    now = dt.datetime(2026, 11, 2, 15, tzinfo=dt.timezone.utc)      # day offset 1 is in progress
    out = dashboard.daily_leaders(con, now_utc=now)
    assert out["day"] == T0.date()
    assert out["wettest"]["city"] == "B" and out["windiest"]["city"] == "A"
    assert out["windiest"]["value"] == 20.0
    # nothing complete when "now" is before every day ends
    assert dashboard.daily_leaders(con, now_utc=dt.datetime(2026, 11, 1, 6, tzinfo=dt.timezone.utc)) is None
