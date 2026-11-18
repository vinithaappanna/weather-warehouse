"""Render the dashboard: one temperature chart and a markdown summary."""
from __future__ import annotations

import datetime as dt

from . import anomalies, extremes

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
                  "Daily average temperature vs the city's other days (|z| >= 2). "
                  "Informational: weather, not a data-quality failure.", "",
                  "| city | day | avg temp C | z-score |", "| --- | --- | ---: | ---: |"]
        for a in unusual:
            lines.append(f"| {a['city']} | {a['day']} | {a['avg_temp_c']} | {a['z']} |")
    wet = extremes.precip_by_city(con)
    if wet:
        lines += ["", "## Precipitation", "",
                  "Model output in mm over the window; the current day includes forecast hours.", "",
                  "| city | total mm | wet days (>=1 mm) |",
                  "| --- | ---: | ---: |"]
        for city, total, days in wet:
            lines.append(f"| {city} | {total} | {days} |")
    severe = extremes.severe_days(con)[:8]
    lines += ["", "## Severe-weather days", "",
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
