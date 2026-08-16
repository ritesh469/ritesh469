#!/usr/bin/env python3
"""Scrape a user's public GitHub contribution calendar (no token needed).

GitHub serves the calendar as an HTML fragment at
https://github.com/users/<username>/contributions -- the same markup the
profile page itself embeds. We parse the day cells with BeautifulSoup and
write data/contributions.json with the raw days plus derived stats
(current streak, longest streak, best day, monthly totals).
"""
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GITHUB_USERNAME", "ritesh469")
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_days(username: str) -> list[dict]:
    resp = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    cells = soup.select("td.ContributionCalendar-day")
    if cells:
        for cell in cells:
            d = cell.get("data-date")
            count = cell.get("data-level")
            level = int(count) if count is not None else 0
            svg_title = cell.find("tool-tip")
            days.append({"date": d, "count": None, "level": level})
    else:
        # Newer markup uses <table> rows of <td> with data-date + data-level attrs on <rect>-less HTML.
        for tile in soup.select("[data-date]"):
            d = tile.get("data-date")
            level = tile.get("data-level")
            if d is None:
                continue
            days.append({"date": d, "count": None, "level": int(level) if level else 0})

    # Try to recover exact counts from tooltip text ("N contributions on <date>").
    tooltip_map = {}
    for tt in soup.select("tool-tip"):
        text = tt.get_text(strip=True)
        for_id = tt.get("for")
        if for_id:
            tooltip_map[for_id] = text

    for cell in soup.select("td.ContributionCalendar-day"):
        cell_id = cell.get("id")
        d = cell.get("data-date")
        if not d or cell_id not in tooltip_map:
            continue
        text = tooltip_map[cell_id]
        first_word = text.split(" ")[0].replace(",", "")
        count = 0 if text.lower().startswith("no contributions") else _safe_int(first_word)
        for day in days:
            if day["date"] == d:
                day["count"] = count

    for day in days:
        if day["count"] is None:
            day["count"] = day["level"]

    days.sort(key=lambda d: d["date"] or "")
    return days


def _safe_int(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        return 0


def derive_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = defaultdict(int)
    for d in days:
        if d["date"]:
            month = d["date"][:7]
            monthly[month] += d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": dict(sorted(monthly.items())),
    }


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    days = fetch_days(username)
    if not days:
        print(f"warning: no contribution cells parsed for {username}", file=sys.stderr)

    stats = derive_stats(days)
    payload = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "contributions.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({len(days)} days, {stats['total']} total contributions)")


if __name__ == "__main__":
    main()
