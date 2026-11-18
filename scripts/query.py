#!/usr/bin/env python3
"""python scripts/query.py city Chicago --days 5 | latest | severe"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from weatherwh.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] if "--db" in sys.argv else ["--db", str(ROOT / "data" / "warehouse.duckdb"), *sys.argv[1:]]))
