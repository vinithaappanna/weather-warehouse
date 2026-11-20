import datetime as dt

from weatherwh import quality, schema_doc, warehouse


def _built():
    con = warehouse.connect(":memory:")
    h = dt.datetime(2026, 11, 1, 12)
    rows = [dict(city="A", hour=h, ingested_at=h, temperature_2m=8.0, precipitation=0.0, wind_speed_10m=5.0)]
    warehouse.record_fetch(con, rows, ["A"], now=h)
    warehouse.refresh(con, rows)
    return con


def test_every_real_column_is_documented():
    con = _built()
    described = schema_doc.describe(con)
    assert [t for t, _ in described] == list(schema_doc.TABLES)       # all documented tables exist
    missing = [(t, c) for t, cols in described for c, _ in cols if c not in schema_doc.COLUMNS]
    assert missing == []
    assert "UNDOCUMENTED" not in schema_doc.render(con)


def test_render_lists_tables_columns_and_types():
    md = schema_doc.render(_built())
    assert "## mart_daily_city" in md and "| total_precip_mm | DOUBLE |" in md
    assert "## fetch_log" in md and "model output" in md


def test_committed_doc_matches_live_schema():
    """docs/data_model.md must be regenerated when a table changes."""
    from pathlib import Path
    doc = Path(__file__).resolve().parents[1] / "docs" / "data_model.md"
    assert doc.exists(), "run scripts/describe_schema.py"
    assert doc.read_text(encoding="utf-8") == schema_doc.render(_built())
