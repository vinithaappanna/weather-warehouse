"""Render the dashboard: one temperature chart and a markdown summary."""
from __future__ import annotations

import datetime as dt

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
    lines += [
        "",
        "![Average temperature by city](avg_temp_by_city.png)",
        "",
        "Data: [Open-Meteo](https://open-meteo.com/) hourly forecast/archive API.",
        "",
    ]
    return "\n".join(lines)


def plot_avg_temp(con, out_path) -> bool:
    rows = con.execute(
        "SELECT day, city, avg_temp_c FROM mart_daily_city ORDER BY day"
    ).fetchall()
    if not rows:
        return False
    by_city: dict[str, list] = {}
    for day, city, temp in rows:
        by_city.setdefault(city, []).append((day, temp))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for city, points in by_city.items():
        ax.plot([p[0] for p in points], [p[1] for p in points], marker="o",
                markersize=3, label=city)
    ax.set_title("Average daily temperature by city")
    ax.set_ylabel("deg C")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True
