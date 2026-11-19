import datetime as dt

from weatherwh import anomalies, dashboard, warehouse


def days(city, temps, start=dt.date(2026, 11, 1)):
    return [(city, start + dt.timedelta(days=i), t) for i, t in enumerate(temps)]


def test_extreme_day_is_flagged_with_sign():
    rows = days("Chicago", [10, 11, 9, 10, 12, 10, 11, -15])
    out = anomalies.find_anomalies(rows)
    assert len(out) == 1
    assert out[0]["day"] == dt.date(2026, 11, 8) and out[0]["z"] < -2


def test_normal_variation_not_flagged():
    assert anomalies.find_anomalies(days("Newark", [5, 15, 6, 14, 5, 15, 6, 14])) == []


def test_short_history_and_flat_baseline_skipped():
    assert anomalies.find_anomalies(days("A", [1, 2, 50])) == []  # too few days
    assert anomalies.find_anomalies(days("B", [5] * 7 + [30])) == []  # zero spread


def test_cities_scored_independently_and_sorted_by_size():
    rows = (days("Hot", [30, 31, 29, 30, 30, 31, 29, 10])
            + days("Cold", [-5, -4, -6, -5, -5, -4, -6, 20]))
    out = anomalies.find_anomalies(rows)
    assert {a["city"] for a in out} == {"Hot", "Cold"}
    assert abs(out[0]["z"]) >= abs(out[1]["z"])


def test_dashboard_lists_unusual_days():
    con = warehouse.connect(":memory:")
    start = dt.datetime(2026, 11, 1)
    temps = [10, 11, 9, 10, 12, 10, 11, -15]
    rows = [{"city": "Chicago", "hour": start + dt.timedelta(days=i), "ingested_at": start,
             "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0}
            for i, t in enumerate(temps)]
    warehouse.refresh(con, rows)
    md = dashboard.render_markdown(con)
    assert "## Unusual days" in md and "Chicago" in md
    con.close()


def test_in_progress_day_is_not_flagged_by_default():
    import datetime as dt
    con = warehouse.connect(":memory:")
    rows = []
    for i in range(10):
        h = dt.datetime(2026, 11, 1 + i, 12)
        t = 10.0 + (i % 3) * 0.1 if i < 9 else 40.0   # last day wildly hot (partial/forecast)
        rows.append({"city": "Chicago", "hour": h, "ingested_at": h,
                     "temperature_2m": t, "precipitation": 0.0, "wind_speed_10m": 5.0})
    warehouse.refresh(con, rows)
    now = dt.datetime(2026, 11, 10, 18, tzinfo=dt.timezone.utc)   # Nov 10 still running in Chicago
    assert anomalies.load_and_find(con, now_utc=now) == []
    flagged = anomalies.load_and_find(con, include_in_progress=True, now_utc=now)
    assert [a["day"] for a in flagged] == [dt.date(2026, 11, 10)]
    later = dt.datetime(2026, 11, 12, 18, tzinfo=dt.timezone.utc)  # day now complete
    assert [a["day"] for a in anomalies.load_and_find(con, now_utc=later)] == [dt.date(2026, 11, 10)]
