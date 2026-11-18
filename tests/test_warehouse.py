import datetime as dt

import pytest

from weatherwh import quality, warehouse

INGESTED = dt.datetime(2026, 11, 15, 12, 0)


def make_rows(city="Newark", day=dt.datetime(2026, 11, 14), hours=3, temp=8.0):
    return [
        {
            "city": city,
            "hour": day + dt.timedelta(hours=h),
            "ingested_at": INGESTED,
            "temperature_2m": temp + h,
            "precipitation": 0.1 * h,
            "wind_speed_10m": 10.0 + h,
        }
        for h in range(hours)
    ]


@pytest.fixture
def con():
    con = warehouse.connect(":memory:")
    yield con
    con.close()


def test_load_raw_is_idempotent(con):
    rows = make_rows()
    assert warehouse.load_raw(con, rows) == 3
    assert warehouse.load_raw(con, rows) == 0  # same city/hour pairs skipped
    assert warehouse.load_raw(con, []) == 0


def test_refresh_builds_daily_mart(con):
    rows = make_rows(hours=3) + make_rows(city="Chicago", temp=2.0)
    warehouse.refresh(con, rows)
    marts = con.execute(
        "SELECT city, hours_observed, avg_temp_c, total_precip_mm "
        "FROM mart_daily_city ORDER BY city"
    ).fetchall()
    assert len(marts) == 2
    chicago = [r for r in marts if r[0] == "Chicago"][0]
    assert chicago[1] == 3
    assert chicago[2] == 3.0  # avg of 2.0, 3.0, 4.0
    assert chicago[3] == 0.3  # 0.0 + 0.1 + 0.2


def test_staging_casts_and_renames(con):
    warehouse.refresh(con, make_rows(hours=1))
    row = con.execute(
        "SELECT temperature_c, precipitation_mm, wind_kmh FROM stg_hourly"
    ).fetchone()
    assert row == (8.0, 0.0, 10.0)


def test_quality_passes_on_clean_data(con):
    warehouse.refresh(con, make_rows(hours=24))
    issues = quality.run_all(con)
    assert issues == []


def test_quality_flags_implausible_temperature(con):
    rows = make_rows(hours=1, temp=500.0)
    warehouse.refresh(con, rows)
    issues = quality.check_temperature_sane(con)
    assert issues and "implausible" in issues[0]


def test_quality_flags_null_temperature(con):
    rows = make_rows(hours=1)
    rows[0]["temperature_2m"] = None
    warehouse.refresh(con, rows)
    assert quality.check_no_null_temperatures(con)


def test_quality_flags_far_future_hours(con):
    rows = make_rows(day=dt.datetime.now() + dt.timedelta(days=10), hours=2)
    warehouse.refresh(con, rows)
    assert quality.check_no_far_future_hours(con)


def test_quality_flags_sparse_days(con):
    warehouse.refresh(con, make_rows(hours=2))
    assert quality.check_full_days(con, expected_hours=20)


def test_export_mart_csv_roundtrip(tmp_path):
    con = warehouse.connect()
    rows = make_rows(hours=4) + make_rows(city="Chicago", hours=2)
    warehouse.refresh(con, rows)
    out = tmp_path / "mart.csv"
    n = warehouse.export_mart_csv(con, out)
    assert n == 2  # two city-days
    import csv as csv_mod
    with open(out, newline="", encoding="utf-8") as fh:
        read = list(csv_mod.DictReader(fh))
    assert {r["city"] for r in read} == {"Newark", "Chicago"}
    assert read[0]["day"] == "2026-11-14"
    con.close()


def test_merge_mart_csv_restores_history(tmp_path):
    import datetime as dt2
    # Day 1: warehouse has old data, snapshot it.
    old = warehouse.connect()
    warehouse.refresh(old, make_rows(day=dt2.datetime(2026, 11, 1), hours=4, temp=5.0))
    snap = tmp_path / "mart.csv"
    warehouse.export_mart_csv(old, snap)
    old.close()

    # Day 2: fresh warehouse (new checkout) only has recent data.
    new = warehouse.connect()
    warehouse.refresh(new, make_rows(day=dt2.datetime(2026, 11, 14), hours=3, temp=9.0))
    merged = warehouse.merge_mart_csv(new, snap)
    assert merged == 1  # the 2026-11-01 Newark city-day came back
    days = [r[0] for r in new.execute(
        "SELECT DISTINCT day FROM mart_daily_city ORDER BY day").fetchall()]
    assert days == [dt2.date(2026, 11, 1), dt2.date(2026, 11, 14)]
    new.close()


def test_merge_mart_csv_fresh_rows_win(tmp_path):
    import datetime as dt2
    old = warehouse.connect()
    warehouse.refresh(old, make_rows(hours=4, temp=5.0))  # 2026-11-14, avg 7.5
    snap = tmp_path / "mart.csv"
    warehouse.export_mart_csv(old, snap)
    old.close()

    new = warehouse.connect()
    warehouse.refresh(new, make_rows(hours=4, temp=20.0))  # same day, newer avg
    merged = warehouse.merge_mart_csv(new, snap)
    assert merged == 0  # nothing new to restore
    avg = new.execute("SELECT avg_temp_c FROM mart_daily_city").fetchone()[0]
    assert avg == 21.5  # fresh rebuild wins over the stale snapshot
    new.close()


def test_merge_mart_csv_missing_file(tmp_path):
    con = warehouse.connect()
    warehouse.refresh(con, make_rows())
    assert warehouse.merge_mart_csv(con, tmp_path / "nope.csv") == 0
    con.close()


def test_exposure_mart_counts_hours_and_degree_hours(con):
    day = dt.datetime(2026, 7, 1)
    temps = [28.0, 30.0, 33.0, -2.0, 0.0, 10.0]
    rows = [{"city": "Chicago", "hour": day + dt.timedelta(hours=h),
             "ingested_at": INGESTED, "temperature_2m": t,
             "precipitation": 0.0, "wind_speed_10m": 5.0}
            for h, t in enumerate(temps)]
    warehouse.refresh(con, rows)
    city, d, heat_h, cold_h, heat_dh, cold_dh = con.execute(
        "SELECT * FROM mart_exposure_city").fetchall()[0]
    assert (city, heat_h, cold_h) == ("Chicago", 2, 2)  # 30 and 33; -2 and 0
    assert heat_dh == 3.0  # (30-30) + (33-30)
    assert cold_dh == 2.0  # (0-(-2)) + (0-0)


def test_exposure_mart_is_per_city_day_and_zero_filled(con):
    rows = make_rows(city="Newark", temp=10.0) + make_rows(city="Chicago", temp=12.0)
    warehouse.refresh(con, rows)
    out = con.execute("SELECT city, heat_hours, cold_hours, heat_degree_hours "
                      "FROM mart_exposure_city ORDER BY city").fetchall()
    assert out == [("Chicago", 0, 0, 0.0), ("Newark", 0, 0, 0.0)]


def test_dashboard_includes_exposure_section(con):
    from weatherwh import dashboard
    warehouse.refresh(con, make_rows(temp=31.0))
    assert "Heat / cold exposure" in dashboard.render_markdown(con)


def test_missing_city_flagged(con):
    warehouse.refresh(con, make_rows(city="Newark"))
    issues = quality.check_all_cities_present(con, expected=["Newark", "Chicago"])
    assert issues == ["no data for city Chicago"]
    assert quality.check_all_cities_present(con, expected=["Newark"]) == []


def test_stale_ingest_flagged_and_fresh_passes(con):
    warehouse.refresh(con, make_rows())  # ingested_at = INGESTED (Nov 15 12:00)
    fresh_now = INGESTED + dt.timedelta(hours=2)
    stale_now = INGESTED + dt.timedelta(hours=30)
    assert quality.check_fresh_ingest(con, now=fresh_now) == []
    issues = quality.check_fresh_ingest(con, now=stale_now)
    assert len(issues) == 1 and "30.0h old" in issues[0]


def test_fresh_ingest_on_empty_warehouse(con):
    warehouse.ensure_raw_table(con)
    assert quality.check_fresh_ingest(con) == ["no ingest timestamps recorded"]
