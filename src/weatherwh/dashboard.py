"""Render the dashboard: one temperature chart and a markdown summary."""
from __future__ import annotations

import datetime as dt

from . import anomalies, extremes

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def daily_leaders(con, now_utc: dt.datetime | None = None) -> dict | None:
    """City leaders (warmest, coldest, wettest, windiest) for the most recent
    day that is complete in every city. In-progress days are skipped because
    they include forecast hours. Ties break on city name. None when no day is
    complete everywhere. Model output."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, max_temp_c, min_temp_c, total_precip_mm, max_wind_kmh "
        "FROM mart_daily_city ORDER BY day DESC, city").fetchall()
    by_day: dict = {}
    for r in rows:
        by_day.setdefault(r[1], []).append(r)
    for day in sorted(by_day, reverse=True):
        cs = by_day[day]
        if all(day_status(c[0], day, now_utc) == "complete" for c in cs):
            def pick(idx, fn):
                best = fn(cs, key=lambda c: ((c[idx] if c[idx] is not None else (-1e9 if fn is max else 1e9)), c[0]))
                return {"city": best[0], "value": best[idx]}
            return {"day": day,
                    "warmest": pick(2, max), "coldest": pick(3, min),
                    "wettest": pick(4, max), "windiest": pick(5, max)}
    return None


def source_freshness(con, now: dt.datetime | None = None) -> list[dict]:
    """Per city: last successful fetch (fetch_log, non-empty responses only),
    its age in hours, the number of failed or empty fetches since that success,
    and the latest weather hour held (normally in the future: forecast). Empty
    when nothing has been logged."""
    now = now or dt.datetime.now()
    try:
        rows = con.execute("SELECT city, fetched_at, rows_returned FROM fetch_log ORDER BY city, fetched_at").fetchall()
    except Exception:
        return []
    latest_hour = dict(con.execute("SELECT city, max(hour) FROM stg_hourly GROUP BY city").fetchall())
    out = []
    for city in sorted({r[0] for r in rows}):
        mine = [r for r in rows if r[0] == city]
        good = [r for r in mine if r[2] and r[2] > 0]
        last = good[-1][1] if good else None
        failed_since = sum(1 for r in mine if (last is None or r[1] > last) and not (r[2] and r[2] > 0))
        out.append({"city": city, "last_success": last,
                    "age_hours": round((now - last).total_seconds() / 3600, 1) if last else None,
                    "failed_since": failed_since, "latest_hour": latest_hour.get(city)})
    return out


def dry_streaks(con, now_utc: dt.datetime | None = None, wet_mm: float = 1.0) -> list[dict]:
    """Per city: current run of consecutive completed days with total rain
    below wet_mm (a "dry" day), and the longest such run in the data.
    In-progress days are skipped (they include forecast hours). Model output;
    wet_mm is illustrative, not a drought measure."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, total_precip_mm FROM mart_daily_city ORDER BY city, day").fetchall()
    per: dict[str, list] = {}
    for city, day, mm in rows:
        if day_status(city, day, now_utc) == "complete":
            per.setdefault(city, []).append((day, mm or 0.0))
    out = []
    for city, days in sorted(per.items()):
        current = 0
        for _day, mm in reversed(days):
            if mm < wet_mm:
                current += 1
            else:
                break
        longest = run = 0
        for _day, mm in days:
            run = run + 1 if mm < wet_mm else 0
            longest = max(longest, run)
        out.append({"city": city, "current_dry_days": current, "longest_dry_days": longest})
    return out


def temperature_records(con, now_utc: dt.datetime | None = None) -> list[dict]:
    """Per city, the warmest and coldest completed day by average temperature
    (in-progress days are skipped: they include forecast hours). Model
    output, within the data window only, not climatological records."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, avg_temp_c FROM mart_daily_city "
        "WHERE avg_temp_c IS NOT NULL ORDER BY city, day").fetchall()
    per: dict[str, list] = {}
    for city, day, avg in rows:
        if day_status(city, day, now_utc) == "complete":
            per.setdefault(city, []).append((day, avg))
    out = []
    for city, days in sorted(per.items()):
        warm = max(days, key=lambda d: (d[1], d[0]))
        cold = min(days, key=lambda d: (d[1], d[0]))
        out.append({"city": city, "warmest_day": warm[0], "warmest_c": warm[1],
                    "coldest_day": cold[0], "coldest_c": cold[1], "days": len(days)})
    return out


def week_over_week_temp(con, now_utc: dt.datetime | None = None, days: int = 7) -> list[dict]:
    """Per city: mean of daily average temperature over the latest `days`
    completed days vs the `days` before them, and the change. Cities without
    2*days completed days are omitted. Model output; compares two short
    windows, not a climate trend."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, avg_temp_c FROM mart_daily_city "
        "WHERE avg_temp_c IS NOT NULL ORDER BY city, day").fetchall()
    per: dict[str, list] = {}
    for city, day, avg in rows:
        if day_status(city, day, now_utc) == "complete":
            per.setdefault(city, []).append(avg)
    out = []
    for city, vals in sorted(per.items()):
        if len(vals) < 2 * days:
            continue
        cur = sum(vals[-days:]) / days
        prev = sum(vals[-2 * days:-days]) / days
        out.append({"city": city, "current_c": round(cur, 2), "previous_c": round(prev, 2),
                    "change_c": round(cur - prev, 2)})
    return out


def degree_days(con, now_utc: dt.datetime | None = None, base_c: float = 18.0) -> list[dict]:
    """Per city over completed days: heating degree days (sum of base minus
    daily average temperature where the day is colder than base) and cooling
    degree days (the reverse). A common load proxy for energy and exposure
    analysis; base 18 C is illustrative, and values are model output over the
    current data window only."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, avg_temp_c FROM mart_daily_city "
        "WHERE avg_temp_c IS NOT NULL ORDER BY city, day").fetchall()
    per: dict[str, dict] = {}
    for city, day, avg in rows:
        if day_status(city, day, now_utc) != "complete":
            continue
        a = per.setdefault(city, {"city": city, "days": 0, "hdd": 0.0, "cdd": 0.0})
        a["days"] += 1
        a["hdd"] += max(0.0, base_c - avg)
        a["cdd"] += max(0.0, avg - base_c)
    return [dict(a, hdd=round(a["hdd"], 1), cdd=round(a["cdd"], 1)) for _c, a in sorted(per.items())]


def wettest_days(con, now_utc: dt.datetime | None = None, n: int = 5) -> list[dict]:
    """The n wettest completed city-days by total precipitation (days with
    no rain are skipped). Model output; in-progress days excluded."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, total_precip_mm FROM mart_daily_city "
        "WHERE total_precip_mm > 0 ORDER BY total_precip_mm DESC, day DESC, city").fetchall()
    out = [{"city": c, "day": d, "precip_mm": mm} for c, d, mm in rows
           if day_status(c, d, now_utc) == "complete"]
    return out[:n]


def windiest_days(con, now_utc: dt.datetime | None = None, n: int = 5) -> list[dict]:
    """The n windiest completed city-days by maximum hourly wind speed.
    Model output; in-progress days excluded."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, max_wind_kmh FROM mart_daily_city "
        "WHERE max_wind_kmh IS NOT NULL ORDER BY max_wind_kmh DESC, day DESC, city").fetchall()
    out = [{"city": c, "day": d, "max_wind_kmh": w} for c, d, w in rows
           if day_status(c, d, now_utc) == "complete"]
    return out[:n]


def temperature_volatility(con, now_utc: dt.datetime | None = None) -> list[dict]:
    """Per city over completed days: mean absolute change in daily average
    temperature between consecutive days (C) and the largest single-day swing
    with its date. Gaps in days are not bridged (only calendar-adjacent days
    count). Model output, current window only."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, avg_temp_c FROM mart_daily_city "
        "WHERE avg_temp_c IS NOT NULL ORDER BY city, day").fetchall()
    per: dict[str, list] = {}
    for city, day, avg in rows:
        if day_status(city, day, now_utc) == "complete":
            per.setdefault(city, []).append((day, avg))
    out = []
    for city, days in sorted(per.items()):
        swings = [(abs(b[1] - a[1]), b[0]) for a, b in zip(days, days[1:]) if (b[0] - a[0]).days == 1]
        if not swings:
            continue
        big = max(swings, key=lambda x: (x[0], x[1]))
        out.append({"city": city, "pairs": len(swings),
                    "mean_change_c": round(sum(x[0] for x in swings) / len(swings), 2),
                    "max_change_c": round(big[0], 2), "max_change_day": big[1]})
    return out


def plot_rain_totals(con, out_path, now_utc: dt.datetime | None = None, wet_days: bool = True) -> bool:
    """Total rain per city over completed days only (in-progress days include
    forecast hours and would skew totals). Bars annotated with the number of
    completed days counted. Model output."""
    from .extremes import day_status

    rows = con.execute("SELECT city, day, total_precip_mm FROM mart_daily_city ORDER BY city, day").fetchall()
    if not rows:
        return False
    per: dict[str, list] = {}
    for city, day, mm in rows:
        if day_status(city, day, now_utc) == "complete":
            a = per.setdefault(city, [0.0, 0])
            a[0] += mm or 0.0
            a[1] += 1
    if not per:
        return False
    cities = sorted(per)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    bars = ax.bar(cities, [per[c][0] for c in cities], color="#1971c2")
    for bar, c in zip(bars, cities):
        ax.annotate(f"{per[c][1]} days", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("total rain (mm)")
    ax.set_title("Total rain per city over completed days (Open-Meteo model output)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True


def render_markdown(con, generated_at: dt.datetime | None = None) -> str:
    generated_at = generated_at or dt.datetime.now(dt.timezone.utc)
    rows = con.execute(
        "SELECT * FROM mart_daily_city ORDER BY day DESC, city LIMIT 30"
    ).fetchall()
    cols = [d[0] for d in con.description]
    lines = [
        "# Weather Warehouse - daily dashboard",
        "",
        f"Generated {generated_at:%Y-%m-%d %H:%M} UTC.",
        "",
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    exposure = con.execute(
        "SELECT city, sum(heat_hours), sum(cold_hours), "
        "round(sum(heat_degree_hours), 1), round(sum(cold_degree_hours), 1) "
        "FROM mart_exposure_city GROUP BY city ORDER BY city"
    ).fetchall()
    if exposure:
        lines += ["", "## Heat / cold exposure (current window)", "",
                  "Hours at or above 30C / at or below 0C and degree-hours beyond "
                  "each threshold. Illustrative thresholds, not clinical guidance.", "",
                  "| city | heat hours | cold hours | heat degree-hours | cold degree-hours |",
                  "| --- | ---: | ---: | ---: | ---: |"]
        for row in exposure:
            lines.append("| " + " | ".join(str(v) for v in row) + " |")
    unusual = anomalies.load_and_find(con)[:8]
    if unusual:
        lines += ["", "## Unusual days", "",
                  "Completed days only: daily average temperature vs the city's other days (|z| >= 2). "
                  "Informational: weather, not a data-quality failure.", "",
                  "| city | day | avg temp C | z-score |", "| --- | --- | ---: | ---: |"]
        for a in unusual:
            lines.append(f"| {a['city']} | {a['day']} | {a['avg_temp_c']} | {a['z']} |")
    wet = extremes.precip_by_city(con)
    if wet:
        lines += ["", "## Precipitation", "",
                  "Model output in mm over the window; the current day includes forecast hours.", "",
                  "![Daily precipitation by city](precip_by_city.png)", "",
                  "| city | total mm | wet days (>=1 mm) |",
                  "| --- | ---: | ---: |"]
        for city, total, days in wet:
            lines.append(f"| {city} | {total} | {days} |")
    lead = daily_leaders(con, now_utc=None)
    if lead:
        lines += ["", f"## City leaders, {lead['day']} (latest day complete in every city)", "",
                  "Model output, not station readings.", "",
                  f"- Warmest high: {lead['warmest']['city']} ({lead['warmest']['value']} C)",
                  f"- Coldest low: {lead['coldest']['city']} ({lead['coldest']['value']} C)",
                  f"- Wettest: {lead['wettest']['city']} ({lead['wettest']['value']} mm)",
                  f"- Windiest: {lead['windiest']['city']} ({lead['windiest']['value']} km/h)"]
    fresh = source_freshness(con)
    if fresh:
        lines += ["", "## Source freshness", "",
                  "Last successful Open-Meteo fetch per city (empty or failed fetches do not count). "
                  "The latest hour is normally ahead of now because the feed includes forecast hours.", "",
                  "| City | Last successful fetch | Age (h) | Failed fetches since | Latest hour held |",
                  "| --- | --- | ---: | ---: | --- |"]
        for f in fresh:
            lines.append(f"| {f['city']} | {f['last_success'] or 'never'} | "
                         f"{f['age_hours'] if f['age_hours'] is not None else '-'} | {f['failed_since']} | "
                         f"{f['latest_hour'] or '-'} |")
    streaks = dry_streaks(con)
    if streaks:
        lines += ["", "## Dry-day streaks (rain under 1 mm)", "",
                  "Consecutive completed days below 1 mm of rain. Model output; illustrative, not a drought measure.", "",
                  "| City | Current streak (days) | Longest streak (days) |", "| --- | ---: | ---: |"]
        for d in streaks:
            lines.append(f"| {d['city']} | {d['current_dry_days']} | {d['longest_dry_days']} |")
    temps = temperature_records(con)
    if temps:
        lines += ["", "## Warmest and coldest completed days", "",
                  "By daily average temperature, within the current data window only. Model output, not climate records.", "",
                  "| City | Warmest day | Avg C | Coldest day | Avg C | Days compared |",
                  "| --- | --- | ---: | --- | ---: | ---: |"]
        for t in temps:
            lines.append(f"| {t['city']} | {t['warmest_day']} | {t['warmest_c']} | "
                         f"{t['coldest_day']} | {t['coldest_c']} | {t['days']} |")
    wow = week_over_week_temp(con)
    if wow:
        lines += ["", "## Week over week temperature", "",
                  "Mean daily average temperature, latest 7 completed days vs the 7 before. Two short windows, model output.", "",
                  "| City | Latest 7 days (C) | Previous 7 days (C) | Change (C) |", "| --- | ---: | ---: | ---: |"]
        for w in wow:
            lines.append(f"| {w['city']} | {w['current_c']} | {w['previous_c']} | {w['change_c']:+.2f} |")
    dd = degree_days(con)
    if dd:
        lines += ["", "## Degree days (base 18 C)", "",
                  "Heating degree days sum how far each completed day's average fell below 18 C; cooling degree days the reverse. "
                  "Illustrative base, model output, current window only.", "",
                  "| City | Days | Heating degree days | Cooling degree days |", "| --- | ---: | ---: | ---: |"]
        for d in dd:
            lines.append(f"| {d['city']} | {d['days']} | {d['hdd']} | {d['cdd']} |")
    wet = wettest_days(con)
    if wet:
        lines += ["", "## Wettest completed days", "", "Model output, current window only.", "",
                  "| City | Day | Precip (mm) |", "| --- | --- | ---: |"]
        for w in wet:
            lines.append(f"| {w['city']} | {w['day']} | {w['precip_mm']} |")
    windy = windiest_days(con)
    if windy:
        lines += ["", "## Windiest completed days", "", "Maximum hourly wind speed. Model output, current window only.", "",
                  "| City | Day | Max wind (km/h) |", "| --- | --- | ---: |"]
        for w in windy:
            lines.append(f"| {w['city']} | {w['day']} | {w['max_wind_kmh']} |")
    vol = temperature_volatility(con)
    if vol:
        lines += ["", "## Day-to-day temperature volatility", "",
                  "Mean absolute change in daily average temperature between consecutive completed days. Model output, current window only.", "",
                  "| City | Day pairs | Mean change (C) | Largest swing (C) | On |", "| --- | ---: | ---: | ---: | --- |"]
        for v in vol:
            lines.append(f"| {v['city']} | {v['pairs']} | {v['mean_change_c']} | {v['max_change_c']} | {v['max_change_day']} |")
    lines += ["", "![Total rain per city](rain_totals.png)", ""]
    lines += ["", "![Daily temperature range by city](temp_range_by_city.png)", ""]
    severe = extremes.severe_days(con)[:8]
    lines += ["", "## Severe-weather days", "",
              "![Daily peak wind by city](wind_by_city.png)", "",
              f"Daily rain >= {extremes.HEAVY_RAIN_MM:g} mm or wind >= "
              f"{extremes.STRONG_WIND_KMH:g} km/h. Illustrative thresholds, not official "
              "weather alerts. Values are Open-Meteo model output in mm and km/h per "
              "city-local day, not gauge observations; a day still in progress includes "
              "forecast hours."]
    if severe:
        lines += ["", "| city | day | precip mm | max wind km/h | why | day status |",
                  "| --- | --- | ---: | ---: | --- | --- |"]
        for a in severe:
            lines.append(f"| {a['city']} | {a['day']} | {a['precip_mm']} | "
                         f"{a['max_wind_kmh']} | {a['reasons']} | {a['status']} |")
    else:
        lines += ["", "None in the current window."]
    lines += [
        "",
        "![Average temperature by city](avg_temp_by_city.png)",
        "",
        "Data: [Open-Meteo](https://open-meteo.com/) hourly forecast API "
        "(past days are model `past_days` output, not observations).",
        "",
    ]
    return "\n".join(lines)


def plot_avg_temp(con, out_path, today: dt.date | None = None) -> bool:
    rows = con.execute(
        "SELECT day, city, avg_temp_c FROM mart_daily_city ORDER BY day"
    ).fetchall()
    if not rows:
        return False
    today = today or dt.date.today()
    last_day = rows[-1][0]
    by_city: dict[str, list] = {}
    for day, city, temp in rows:
        by_city.setdefault(city, []).append((day, temp))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for city, points in by_city.items():
        ax.plot([p[0] for p in points], [p[1] for p in points], marker="o",
                markersize=3, label=city)
    if today <= last_day:
        # Shade from start of today through the end of the last data day so the
        # forecast region is visible even when it covers only today.
        ax.axvspan(today - dt.timedelta(days=0.5), last_day + dt.timedelta(days=0.5),
                   color="grey", alpha=0.15)
        mid = today + (last_day - today) / 2
        ax.annotate("forecast", xy=(mid, ax.get_ylim()[0] + 1),
                    ha="center", fontsize=8, color="dimgrey")
    ax.set_title("Average daily temperature by city (Open-Meteo forecast model data; shaded = forecast)\n"
                 "past days are model past_days output, not ground-station observations",
                 fontsize=11)
    ax.set_ylabel("deg C")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True


def _plot_daily_bars(con, column: str, out_path, ylabel: str, title: str,
                     now_utc: dt.datetime | None = None, ref_line: float | None = None,
                     ref_label: str = "") -> bool:
    """Grouped daily bars per city for one mart column. Days still in progress
    for a city (they include forecast hours) are hatched and lighter so they are
    not read as observed totals. Model output."""
    from .extremes import day_status

    rows = con.execute(
        f"SELECT day, city, {column} FROM mart_daily_city ORDER BY day, city").fetchall()
    if not rows:
        return False
    days = sorted({r[0] for r in rows})
    cities = sorted({r[1] for r in rows})
    val = {(r[0], r[1]): r[2] or 0.0 for r in rows}
    width = 0.8 / len(cities)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    seen = set()
    for ci, city in enumerate(cities):
        color = f"C{ci}"
        for di, day in enumerate(days):
            if (day, city) not in val:
                continue
            partial = day_status(city, day, now_utc) != "complete"
            ax.bar(di + ci * width, val[(day, city)], width, color=color,
                   alpha=0.45 if partial else 1.0, hatch="//" if partial else None,
                   edgecolor="grey" if partial else color,
                   label=city if city not in seen else None)
            seen.add(city)
    if ref_line is not None:
        ax.axhline(ref_line, color="black", linestyle="--", linewidth=1, label=ref_label)
    ax.set_xticks([i + 0.4 - width / 2 for i in range(len(days))])
    ax.set_xticklabels([str(d)[5:] for d in days], rotation=60, fontsize=7)
    ax.legend(fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title + "\nhatched = day in progress, includes forecast hours", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True


def plot_precip(con, out_path, now_utc: dt.datetime | None = None) -> bool:
    """Daily precipitation per city (mm, model output)."""
    return _plot_daily_bars(con, "total_precip_mm", out_path, "mm per city-local day",
                            "Daily precipitation by city (Open-Meteo model output)", now_utc)


def plot_wind(con, out_path, now_utc: dt.datetime | None = None) -> bool:
    """Daily peak wind per city (km/h, model output) with the illustrative
    strong-wind threshold as a reference line (not an official alert level)."""
    from .extremes import STRONG_WIND_KMH
    return _plot_daily_bars(con, "max_wind_kmh", out_path, "peak km/h per city-local day",
                            "Daily peak wind by city (Open-Meteo model output)", now_utc,
                            ref_line=STRONG_WIND_KMH,
                            ref_label=f"{STRONG_WIND_KMH:g} km/h (illustrative, not an alert)")


def plot_temp_range(con, out_path, now_utc: dt.datetime | None = None) -> bool:
    """Daily min-max temperature band and mean line per city (deg C, model
    output). Days still in progress include forecast hours, so their mean
    marker is hollow and the band is not to be read as an observed range."""
    from .extremes import day_status

    rows = con.execute(
        "SELECT city, day, min_temp_c, avg_temp_c, max_temp_c FROM mart_daily_city "
        "ORDER BY city, day").fetchall()
    if not rows:
        return False
    cities = sorted({r[0] for r in rows})
    fig, axes = plt.subplots(len(cities), 1, figsize=(9, 2.2 * len(cities)), sharex=True,
                             squeeze=False)
    for ax, city in zip(axes[:, 0], cities):
        pts = [r for r in rows if r[0] == city]
        x = list(range(len(pts)))
        ax.fill_between(x, [p[2] for p in pts], [p[4] for p in pts], alpha=0.25)
        ax.plot(x, [p[3] for p in pts], color="C0", linewidth=1)
        for i, p in enumerate(pts):
            partial = day_status(city, p[1], now_utc) != "complete"
            ax.plot(i, p[3], "o", markersize=4, color="C0",
                    markerfacecolor="white" if partial else "C0")
        ax.set_ylabel(city, fontsize=8)
        ax.grid(alpha=0.3)
    days = [r[1] for r in rows if r[0] == cities[0]]
    axes[-1, 0].set_xticks(range(len(days)))
    axes[-1, 0].set_xticklabels([str(d)[5:] for d in days], rotation=60, fontsize=7)
    axes[0, 0].set_title("Daily min-max and mean temperature, deg C (Open-Meteo model output)\n"
                         "hollow marker = day in progress, includes forecast hours", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True
