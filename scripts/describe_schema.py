#!/usr/bin/env python3
"""Regenerate docs/data_model.md from the warehouse schema."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import duckdb

from weatherwh import schema_doc

con = duckdb.connect(str(ROOT / "data" / "warehouse.duckdb"), read_only=True)
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "data_model.md").write_text(schema_doc.render(con), encoding="utf-8")
print("wrote docs/data_model.md")
