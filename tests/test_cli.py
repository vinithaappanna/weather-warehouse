import datetime as dt

from weatherwh import cli, warehouse


def _con():
    con = warehouse.connect(":memory:")
    rows = []
    for city, day, p in [("Chicago", 1, 0.0), ("Chicago", 2, 12.0), ("Newark", 2, 1.0)]:
        h = dt.datetime(2026, 11, day, 12)
        rows.append(dict(city=city, hour=h, ingested_at=h, temperature_2m=8.0,
                         precipitation=p, wind_speed_10m=5.0))
    warehouse.refresh(con, rows)
    return con


def test_city_history_newest_first_case_insensitive():
    out = cli.city_history(_con(), "chicago", days=5)
    assert [str(r["day"]) for r in out] == ["2026-11-02", "2026-11-01"]
    assert out[0]["status"] == "complete"


def test_latest_by_city_one_row_each():
    out = cli.latest_by_city(_con())
    assert [(r["city"], str(r["day"])) for r in out] == [("Chicago", "2026-11-02"), ("Newark", "2026-11-02")]


def test_main_outputs_and_exit_codes(capsys):
    con = _con()
    assert cli.main(["city", "Chicago"], con=con) == 0
    assert "rain 12.0 mm" in capsys.readouterr().out
    assert cli.main(["city", "Nowhere"], con=con) == 1
    capsys.readouterr()
    assert cli.main(["severe"], con=con) == 0
    out = capsys.readouterr().out
    assert "heavy rain" in out and "not official weather alerts" in out


def test_dry_subcommand_prints_streaks_and_caveat(capsys):
    import datetime as dt
    from weatherwh import cli, warehouse
    con = warehouse.connect(":memory:")
    t0 = dt.datetime(2026, 1, 1)
    warehouse.refresh(con, [{"city": "New York", "hour": t0 + dt.timedelta(days=d), "ingested_at": t0,
                             "temperature_2m": 5.0, "precipitation": 0.0, "wind_speed_10m": 5.0} for d in range(3)])
    assert cli.main(["dry"], con=con) == 0
    out = capsys.readouterr().out
    assert "New York" in out and "3 days" in out and "1 mm/day" in out and "same illustrative cutoff" in out
