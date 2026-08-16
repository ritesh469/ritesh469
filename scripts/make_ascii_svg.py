#!/usr/bin/env python3
"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps brightness to a density
ramp, and wraps each row in a clip-path wipe that reveals left-to-right,
staggered top-to-bottom, with a small block cursor riding the wipe edge.
The portrait prints once and freezes -- no looping.
"""
import sys
from pathlib import Path

from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = blank
COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11
FILL = "#8b949e"
CURSOR_FILL = "#c9d1d9"
ROW_DURATION = 0.55
ROW_STAGGER = 0.09


def image_to_rows(path: str, cols: int = COLS, rows: int = ROWS) -> list[str]:
    img = Image.open(path).convert("L").resize((cols, rows), Image.LANCZOS)
    pixels = list(img.getdata())
    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        row_pixels = pixels[r * cols:(r + 1) * cols]
        chars = []
        for p in row_pixels:
            idx = min(ramp_len - 1, (255 - p) * ramp_len // 256)
            chars.append(RAMP[idx])
        lines.append("".join(chars))
    return lines


def escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines: list[str], static: bool = False) -> str:
    width = COLS * CHAR_W + 20
    height = ROWS * CHAR_H + 20
    parts = [
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Consolas, monospace">',
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="transparent"/>',
        f'<style>text{{font-size:{CHAR_H}px;fill:{FILL};white-space:pre;}}</style>',
    ]

    total_width = COLS * CHAR_W

    for i, line in enumerate(lines):
        y = 10 + (i + 1) * CHAR_H - 2
        row_id = f"row{i}"
        start = i * ROW_STAGGER
        end = start + ROW_DURATION
        safe_line = escape(line)

        if static:
            parts.append(
                f'<text x="10" y="{y:.1f}">{safe_line}</text>'
            )
            continue

        parts.append(f'<clipPath id="clip{row_id}">')
        parts.append(
            f'<rect x="10" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H + 4}">'
            f'<animate attributeName="width" from="0" to="{total_width:.1f}" '
            f'begin="{start:.2f}s" dur="{ROW_DURATION:.2f}s" fill="freeze" calcMode="linear"/>'
            f'</rect>'
        )
        parts.append('</clipPath>')
        parts.append(
            f'<text x="10" y="{y:.1f}" clip-path="url(#clip{row_id})">{safe_line}</text>'
        )
        # Cursor block riding the wipe edge, disappears when the row finishes.
        parts.append(
            f'<rect x="10" y="{y - CHAR_H + 1:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" '
            f'fill="{CURSOR_FILL}" opacity="0">'
            f'<animate attributeName="x" from="10" to="{10 + total_width - CHAR_W:.1f}" '
            f'begin="{start:.2f}s" dur="{ROW_DURATION:.2f}s" fill="freeze" calcMode="linear"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.9;1" '
            f'begin="{start:.2f}s" dur="{ROW_DURATION:.2f}s" fill="freeze"/>'
            f'</rect>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    static = __import__("os").environ.get("STATIC") == "1"
    lines = image_to_rows(src)
    svg = build_svg(lines, static=static)
    out = Path("avi-ascii.svg")
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(lines)} rows x {COLS} cols)")
