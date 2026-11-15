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
