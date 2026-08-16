#!/usr/bin/env python3
"""Render data/contributions.json as a 53-week x 7-day heatmap SVG.

Boxes are rounded and colored with a GitHub-ish green ramp, revealed once
with a diagonal, line-after-line slide-down (CSS keyframes that play on
load then freeze -- no looping), plus a Less->More legend and a stats
footer.
"""
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end)

CELL = 12
GAP = 3
LEFT_PAD = 32
TOP_PAD = 30
BOTTOM_PAD = 46
RIGHT_PAD = 16
WEEKS = 53
DAYS = 7

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for_count(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    if max_count <= 0:
        return 1
    ratio = count / max_count
    if ratio > 0.75:
        return 5
    if ratio > 0.5:
        return 4
    if ratio > 0.25:
        return 3
    return 2 if count > 0 else 1


def load_data() -> dict:
    path = Path("data/contributions.json")
    return json.loads(path.read_text(encoding="utf-8"))


def build_grid(days: list[dict]) -> list[list[dict | None]]:
    """Return grid[week][weekday] aligned like GitHub's calendar (Sun-Sat columns)."""
    by_date = {d["date"]: d for d in days if d.get("date")}
    if not by_date:
        return []

    all_dates = sorted(by_date.keys())
    end = datetime.strptime(all_dates[-1], "%Y-%m-%d").date()
    start = end - timedelta(weeks=WEEKS - 1)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back up to Sunday

    grid: list[list[dict | None]] = []
    cursor = start
    for _w in range(WEEKS):
        week = []
        for _d in range(DAYS):
            key = cursor.isoformat()
            week.append(by_date.get(key))
            cursor += timedelta(days=1)
        grid.append(week)
    return grid


def build_svg(payload: dict, static: bool = False) -> str:
    days = payload.get("days", [])
    stats = payload.get("stats", {})
    grid = build_grid(days)
    max_count = max((d["count"] for d in days if d), default=0)

    width = LEFT_PAD + WEEKS * (CELL + GAP) + RIGHT_PAD
    height = TOP_PAD + DAYS * (CELL + GAP) + BOTTOM_PAD

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Consolas, monospace">',
        f'<rect width="{width}" height="{height}" fill="transparent"/>',
    ]

    if not static:
        parts.append(
            '<style>'
            '.cell{opacity:0;transform:translate(-6px,-6px);animation:cellIn 0.4s ease-out forwards;}'
            '@keyframes cellIn{to{opacity:1;transform:translate(0,0);}}'
            '</style>'
        )

    # Month labels along the top, placed at the first week column that starts a new month.
    last_month = None
    for w, week in enumerate(grid):
        first_day = next((d for d in week if d), None)
        if not first_day:
            continue
        d = datetime.strptime(first_day["date"], "%Y-%m-%d").date()
        if d.day <= 7 and d.month != last_month:
            x = LEFT_PAD + w * (CELL + GAP)
            parts.append(
                f'<text x="{x}" y="{TOP_PAD - 10}" font-size="10" fill="#8b949e">{MONTH_LABELS[d.month - 1]}</text>'
            )
            last_month = d.month

    for w, week in enumerate(grid):
        for wd, day in enumerate(week):
            x = LEFT_PAD + w * (CELL + GAP)
            y = TOP_PAD + wd * (CELL + GAP)
            level = level_for_count(day["count"], max_count) if day else 0
            color = PALETTE[level]
            title = ""
            if day:
                title = f'{day["count"]} contributions on {day["date"]}'
            delay = (w + wd) * 0.012
            cls = "" if static else 'class="cell"'
            style = "" if static else f'style="animation-delay:{delay:.3f}s"'
            parts.append(
                f'<rect {cls} {style} x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{color}"><title>{title}</title></rect>'
            )

    # Legend: Less -> More
    legend_y = height - 24
    legend_x = width - RIGHT_PAD - (len(PALETTE) * (CELL + GAP)) - 60
    parts.append(f'<text x="{legend_x - 36}" y="{legend_y + 10}" font-size="10" fill="#8b949e">Less</text>')
    for i, color in enumerate(PALETTE):
        x = legend_x + i * (CELL + GAP)
        parts.append(f'<rect x="{x}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
    parts.append(
        f'<text x="{legend_x + len(PALETTE) * (CELL + GAP) + 6}" y="{legend_y + 10}" '
        f'font-size="10" fill="#8b949e">More</text>'
    )

    total = stats.get("total", 0)
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    footer = f"{total:,} contributions in the last year  ·  current streak {current_streak}d  ·  longest streak {longest_streak}d"
    parts.append(f'<text x="{LEFT_PAD}" y="{height - 8}" font-size="11" fill="#c9d1d9">{footer}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    payload = load_data()
    svg = build_svg(payload, static=static)
    out = Path("contrib-heatmap.svg")
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")
