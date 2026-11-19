#!/usr/bin/env python3
"""Demo: join SYNTHETIC daily claim counts to the weather mart.
The wet-day uplift is assumed by the generator, so this shows the join
mechanics only. It is not evidence that weather changes claims."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import duckdb

from weatherwh import claims_link

con = duckdb.connect(str(ROOT / "data" / "warehouse.duckdb"), read_only=True)
days = con.execute("SELECT city, day, total_precip_mm FROM mart_daily_city").fetchall()
claims = claims_link.synthetic_claims(days)
print("city           wet days  dry days  mean claims wet / dry   (synthetic, completed days only)")
for r in claims_link.wet_vs_dry(con, claims):
    print(f"{r['city']:<14} {r['wet_days']:>8} {r['dry_days']:>9}   {r['wet_mean']} / {r['dry_mean']}")
