#!/usr/bin/env python3
"""Hand-authored neofetch-style SVG info card.

A title bar plus colored key/value rows (Now, Prev, Stack, Highlights) that
fade and slide in on a short stagger, as if printing next to the portrait.
Set STATIC=1 to emit a frozen frame for local Quick Look previews.
"""
import os
from pathlib import Path

WIDTH = 490
LINE_H = 26
PAD_X = 24
TITLE_H = 44

BG = "#0d1117"
BORDER = "#30363d"
TITLE_BG = "#161b22"
KEY_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
DIM_COLOR = "#8b949e"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]

# --- Edit this content freely -------------------------------------------
USER = "ritesh469@github"
ROWS = [
    ("Now", "Software Engineer, building AI/agent tooling"),
    ("Prev", "Backend + ML systems"),
    ("Stack", "Python, TypeScript, React, PostgreSQL"),
    ("Highlights", "Shipped 3 production ML pipelines"),
    ("Highlights", "Open-source contributor"),
    ("Focus", "LLM applications & developer tooling"),
]
# --------------------------------------------------------------------------

LINE_DURATION = 0.35
LINE_STAGGER = 0.18


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static: bool = False) -> str:
    height = TITLE_H + PAD_X + (len(ROWS) + 1) * LINE_H + PAD_X

    parts = [
        f'<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Consolas, monospace">',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0.5 {TITLE_H} V8.5 A8 8 0 0 1 8.5 0.5 H{WIDTH - 8.5} '
        f'A8 8 0 0 1 {WIDTH - 0.5} 8.5 V{TITLE_H} Z" fill="{TITLE_BG}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{WIDTH}" y2="{TITLE_H}" stroke="{BORDER}"/>',
    ]

    for i, color in enumerate(DOT_COLORS):
        cx = 22 + i * 20
        parts.append(f'<circle cx="{cx}" cy="{TITLE_H / 2:.0f}" r="6" fill="{color}"/>')

    parts.append(
        f'<text x="{WIDTH / 2:.0f}" y="{TITLE_H / 2 + 4:.0f}" text-anchor="middle" '
        f'font-size="13" fill="{DIM_COLOR}">neofetch</text>'
    )

    y0 = TITLE_H + PAD_X + LINE_H - 6
    parts.append(
        f'<text x="{PAD_X}" y="{y0}" font-size="15" font-weight="bold" fill="{VALUE_COLOR}">{escape(USER)}</text>'
    )
    parts.append(
        f'<line x1="{PAD_X}" y1="{y0 + 8}" x2="{WIDTH - PAD_X}" y2="{y0 + 8}" stroke="{BORDER}"/>'
    )

    label_w = max(len(k) for k, _ in ROWS) + 2

    for i, (key, value) in enumerate(ROWS):
        y = y0 + (i + 2) * LINE_H - 6
        start = i * LINE_STAGGER
        line_svg = (
            f'<text x="{PAD_X}" y="{y}" font-size="14">'
            f'<tspan fill="{KEY_COLOR}" font-weight="bold">{escape(key)}</tspan>'
            f'<tspan fill="{DIM_COLOR}">{"." * (label_w - len(key))}</tspan>'
            f'<tspan fill="{VALUE_COLOR}"> {escape(value)}</tspan>'
            f'</text>'
        )
        if static:
            parts.append(line_svg)
            continue

        parts.append(
            f'<g opacity="0" transform="translate(-8,0)">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{start:.2f}s" '
            f'dur="{LINE_DURATION:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-8,0" to="0,0" begin="{start:.2f}s" dur="{LINE_DURATION:.2f}s" fill="freeze"/>'
            f'{line_svg}'
            f'</g>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static=static)
    out = Path("info-card.svg")
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")
