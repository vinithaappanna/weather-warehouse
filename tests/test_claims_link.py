import datetime as dt

from weatherwh import claims_link, warehouse

D = dt.date


def _con(spec):
    con = warehouse.connect(":memory:")
    rows = []
    for city, day, p in spec:
        h = dt.datetime(2026, 11, day, 12)
        rows.append(dict(city=city, hour=h, ingested_at=h, temperature_2m=8.0,
                         precipitation=p, wind_speed_10m=5.0))
    warehouse.refresh(con, rows)
    return con


def test_synthetic_claims_deterministic_and_uplifted():
    days = [("A", D(2026, 1, 1), 5.0)] * 400 + [("A", D(2026, 1, 2), 0.0)] * 400
    a = claims_link.synthetic_claims(days, seed=1)
    assert a == claims_link.synthetic_claims(days, seed=1)
    wet = sum(n for _, d, n in a if d.day == 1) / 400
    dry = sum(n for _, d, n in a if d.day == 2) / 400
    assert wet > dry and abs(dry - 20) < 1.5 and abs(wet - 25) < 1.5


def test_wet_vs_dry_groups_and_drops_unknown_and_in_progress():
    con = _con([("A", 1, 0.0), ("A", 2, 5.0), ("A", 3, 0.5), ("B", 1, 3.0)])
    claims = [("A", D(2026, 11, 1), 10), ("A", D(2026, 11, 2), 30), ("A", D(2026, 11, 3), 20),
              ("A", D(2026, 11, 9), 99),            # no mart row: dropped
              ("B", D(2026, 11, 1), 8)]
    now = dt.datetime(2026, 11, 20, 12, tzinfo=dt.timezone.utc)
    out = {r["city"]: r for r in claims_link.wet_vs_dry(con, claims, now_utc=now)}
    assert out["A"] == {"city": "A", "wet_days": 1, "dry_days": 2, "wet_mean": 30.0, "dry_mean": 15.0}
    assert out["B"]["dry_mean"] is None and out["B"]["wet_mean"] == 8.0   # missing group is None


def test_in_progress_day_is_excluded():
    con = _con([("A", 1, 0.0), ("A", 2, 9.0)])
    now = dt.datetime(2026, 11, 2, 15, tzinfo=dt.timezone.utc)   # Nov 2 still running for A (UTC fallback)
    out = claims_link.wet_vs_dry(con, [("A", D(2026, 11, 1), 5), ("A", D(2026, 11, 2), 50)], now_utc=now)
    assert out == [{"city": "A", "wet_days": 0, "dry_days": 1, "wet_mean": None, "dry_mean": 5.0}]
