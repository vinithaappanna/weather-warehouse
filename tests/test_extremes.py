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


def test_source_freshness_counts_failures_since_last_success():
    con = warehouse.connect(":memory:")
    assert dashboard.source_freshness(con) == []
    load(con, [("A", 0, 0.0, 5.0), ("B", 0, 0.0, 5.0)])
    t = dt.datetime(2026, 11, 2, 12)
    warehouse.record_fetch(con, [{"city": "A", "hour": t}, {"city": "B", "hour": t}], ["A", "B"], now=t)
    # next fetch: A returns nothing (failed/empty), B succeeds again; C never succeeds
    warehouse.record_fetch(con, [{"city": "B", "hour": t}], ["A", "B", "C"], now=t + dt.timedelta(hours=3))
    out = {f["city"]: f for f in dashboard.source_freshness(con, now=t + dt.timedelta(hours=5))}
    assert out["A"]["last_success"] == t and out["A"]["age_hours"] == 5.0 and out["A"]["failed_since"] == 1
    assert out["B"]["age_hours"] == 2.0 and out["B"]["failed_since"] == 0
    assert out["C"]["last_success"] is None and out["C"]["age_hours"] is None and out["C"]["failed_since"] == 1
    assert "## Source freshness" in dashboard.render_markdown(con)


def test_dry_streaks_current_and_longest_complete_days_only():
    con = warehouse.connect(":memory:")
    # A: dry, dry, wet, dry, dry; B: wet, dry
    load(con, [("A", 0, 0.0, 5.0), ("A", 1, 0.5, 5.0), ("A", 2, 3.0, 5.0),
               ("A", 3, 0.0, 5.0), ("A", 4, 0.2, 5.0),
               ("B", 3, 2.0, 5.0), ("B", 4, 0.0, 5.0)])
    now = dt.datetime(2026, 11, 5, 12, tzinfo=dt.timezone.utc)   # day offset 4 is in progress
    out = {d["city"]: d for d in dashboard.dry_streaks(con, now_utc=now)}
    assert out["A"] == {"city": "A", "current_dry_days": 1, "longest_dry_days": 2}   # 11-04 dry, 11-03 wet
    assert out["B"]["longest_dry_days"] == 0
    # with a later "now" day 4 completes: A's current streak is 2
    later = dt.datetime(2026, 11, 6, 12, tzinfo=dt.timezone.utc)
    out2 = {d["city"]: d for d in dashboard.dry_streaks(con, now_utc=later)}
    assert out2["A"]["current_dry_days"] == 2 and out2["B"]["current_dry_days"] == 1
    assert "Dry-day streaks" in dashboard.render_markdown(con)


def test_plot_rain_totals_completed_days_only(tmp_path):
    con = warehouse.connect(":memory:")
    assert dashboard.plot_rain_totals(_empty(), tmp_path / "e.png") is False
    load(con, [("A", 0, 2.0, 5.0), ("A", 1, 1.0, 5.0), ("B", 0, 0.5, 5.0)])
    now = dt.datetime(2026, 11, 2, 12, tzinfo=dt.timezone.utc)   # day offset 1 in progress: excluded
    assert dashboard.plot_rain_totals(con, tmp_path / "r.png", now_utc=now) is True
    assert (tmp_path / "r.png").stat().st_size > 1000
    assert "rain_totals.png" in dashboard.render_markdown(con)


def test_temperature_records_complete_days_only():
    con = warehouse.connect(":memory:")
    rows = [{"city": "A", "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
             "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0}
            for d, t in [(0, 8.0), (1, 15.0), (2, 3.0), (3, 30.0)]]
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)   # day offset 3 in progress: excluded
    out = dashboard.temperature_records(con, now_utc=now)
    assert out == [{"city": "A", "warmest_day": dt.date(2026, 11, 2), "warmest_c": 15.0,
                    "coldest_day": dt.date(2026, 11, 3), "coldest_c": 3.0, "days": 3}]
    assert "Warmest and coldest completed days" in dashboard.render_markdown(con)
    assert dashboard.temperature_records(_empty()) == []
    con.close()


def test_week_over_week_temp_windows_and_omission():
    con = warehouse.connect(":memory:")
    temps = [10.0] * 3 + [14.0] * 3          # days=3: previous 10, latest 14
    rows = [{"city": "A", "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
             "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0}
            for d, t in enumerate(temps)]
    rows += [{"city": "B", "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
              "temperature_2m": 5.0, "precipitation": 0.0, "wind_speed_10m": 5.0} for d in range(4)]
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 10, 12, tzinfo=dt.timezone.utc)   # all days complete
    out = dashboard.week_over_week_temp(con, now_utc=now, days=3)
    assert out == [{"city": "A", "current_c": 14.0, "previous_c": 10.0, "change_c": 4.0}]   # B too short
    assert dashboard.week_over_week_temp(_empty()) == []
    con.close()


def test_degree_days_base_completed_days_and_render():
    con = warehouse.connect(":memory:")
    rows = [{"city": "A", "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
             "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0}
            for d, t in [(0, 8.0), (1, 20.0), (2, 18.0), (3, 40.0)]]
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)   # day offset 3 in progress: excluded
    assert dashboard.degree_days(con, now_utc=now) == [{"city": "A", "days": 3, "hdd": 10.0, "cdd": 2.0}]
    assert dashboard.degree_days(con, now_utc=now, base_c=10.0) == [{"city": "A", "days": 3, "hdd": 2.0, "cdd": 18.0}]
    assert "Degree days (base 18 C)" in dashboard.render_markdown(con)
    assert dashboard.degree_days(_empty()) == []
    con.close()


def test_wettest_days_order_skips_dry_and_in_progress():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 1.0, 5.0), ("A", 1, 0.0, 5.0), ("B", 0, 3.0, 5.0), ("B", 2, 9.0, 5.0)])
    now = dt.datetime(2026, 11, 3, 12, tzinfo=dt.timezone.utc)   # offset 2 in progress
    out = dashboard.wettest_days(con, now_utc=now)
    assert [(w["city"], w["precip_mm"]) for w in out] == [("B", 3.0), ("A", 1.0)]
    assert all(w["precip_mm"] > 0 for w in out) and dashboard.wettest_days(con, now_utc=now, n=1)[0]["city"] == "B"
    assert dashboard.wettest_days(_empty()) == []
    con.close()


def test_windiest_days_order_and_in_progress_excluded():
    con = warehouse.connect(":memory:")
    load(con, [("A", 0, 0.0, 30.0), ("B", 0, 0.0, 60.0), ("A", 2, 0.0, 99.0)])
    now = dt.datetime(2026, 11, 3, 12, tzinfo=dt.timezone.utc)   # offset 2 in progress
    out = dashboard.windiest_days(con, now_utc=now)
    assert [(w["city"], w["max_wind_kmh"]) for w in out] == [("B", 60.0), ("A", 30.0)]
    assert dashboard.windiest_days(con, now_utc=now, n=1)[0]["city"] == "B"
    assert dashboard.windiest_days(_empty()) == []
    con.close()


def test_temperature_volatility_adjacent_days_only():
    con = warehouse.connect(":memory:")
    rows = [{"city": "A", "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
             "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0}
            for d, t in [(0, 10.0), (1, 14.0), (2, 13.0), (5, 30.0)]]      # day 5 not adjacent to day 2
    rows += [{"city": "B", "hour": T0, "ingested_at": T0, "temperature_2m": 5.0,
              "precipitation": 0.0, "wind_speed_10m": 5.0}]                 # single day: omitted
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 10, 12, tzinfo=dt.timezone.utc)
    out = dashboard.temperature_volatility(con, now_utc=now)
    assert out == [{"city": "A", "pairs": 2, "mean_change_c": 2.5, "max_change_c": 4.0,
                    "max_change_day": dt.date(2026, 11, 2)}]
    assert dashboard.temperature_volatility(_empty()) == []
    con.close()


def test_frost_days_threshold_inclusive_completed_only():
    con = warehouse.connect(":memory:")
    rows = [{"city": "A", "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
             "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0}
            for d, t in [(0, 0.0), (1, 5.0), (2, -3.0), (3, -20.0)]]       # day 3 in progress
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)
    assert dashboard.frost_days(con, now_utc=now) == [
        {"city": "A", "days": 3, "frost_days": 2, "share": 0.6667, "coldest_c": -3.0, "coldest_day": dt.date(2026, 11, 3)}]
    assert dashboard.frost_days(con, now_utc=now, freeze_c=-5.0)[0]["frost_days"] == 0
    assert dashboard.frost_days(_empty()) == []
    con.close()


def test_city_temp_correlation_pairs_and_skips():
    con = warehouse.connect(":memory:")
    rows = []
    for d in range(6):
        for city, t in [("A", float(d)), ("B", 2.0 * d + 1), ("C", float(-d)), ("D", 5.0)]:
            rows.append({"city": city, "hour": T0 + dt.timedelta(days=d), "ingested_at": T0,
                         "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0})
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 20, 12, tzinfo=dt.timezone.utc)
    got = {(r["city_a"], r["city_b"]): r["r"] for r in dashboard.city_temp_correlation(con, now_utc=now)}
    assert got == {("A", "B"): 1.0, ("A", "C"): -1.0, ("B", "C"): -1.0}   # D constant, skipped
    assert dashboard.city_temp_correlation(con, now_utc=now, min_days=7) == []
    assert dashboard.city_temp_correlation(_empty()) == []
    con.close()
