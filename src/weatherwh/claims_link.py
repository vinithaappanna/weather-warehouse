"""Join a daily claims-count table to the weather mart (illustrative demo).

The shipped generator builds SYNTHETIC claim counts with a wet-day uplift that
it assumes itself. The demo therefore shows how to join and compare, not that
weather changes claims. Real use would load real aggregate counts from your
own source. Only completed city-local days are compared; an in-progress day
includes forecast hours and would mix observed and forecast values.
"""
from __future__ import annotations

import datetime as dt
import math
import random

WET_MM = 1.0  # a "wet" day has at least this much model-output rain


def _poisson(rng: random.Random, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def synthetic_claims(days: list[tuple[str, dt.date, float]], base: float = 20.0,
                     wet_uplift: float = 0.25, seed: int = 7) -> list[tuple[str, dt.date, int]]:
    """(city, day, claims) from (city, day, precip_mm). Deterministic per seed."""
    rng = random.Random(seed)
    return [(c, d, _poisson(rng, base * (1 + wet_uplift if (p or 0) >= WET_MM else 1)))
            for c, d, p in days]


def wet_vs_dry(con, claims: list[tuple[str, dt.date, int]], now_utc: dt.datetime | None = None) -> list[dict]:
    """Per city: mean claims on wet vs dry completed days, with day counts.
    Days with no mart row, or not yet complete, are dropped. Cities missing
    wet or dry days report None for the missing mean."""
    from .extremes import day_status

    mart = {(c, d): p for c, d, p in con.execute(
        "SELECT city, day, total_precip_mm FROM mart_daily_city").fetchall()}
    groups: dict[str, dict[str, list[int]]] = {}
    for city, day, n in claims:
        precip = mart.get((city, day))
        if precip is None or day_status(city, day, now_utc) != "complete":
            continue
        g = groups.setdefault(city, {"wet": [], "dry": []})
        g["wet" if precip >= WET_MM else "dry"].append(n)
    out = []
    for city in sorted(groups):
        w, d = groups[city]["wet"], groups[city]["dry"]
        out.append({"city": city, "wet_days": len(w), "dry_days": len(d),
                    "wet_mean": round(sum(w) / len(w), 2) if w else None,
                    "dry_mean": round(sum(d) / len(d), 2) if d else None})
    return out
