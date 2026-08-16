#!/usr/bin/env python3
"""Prep a source photo for ASCII conversion: remove background, boost local
contrast, and composite onto white so the background maps to blank ASCII."""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep(src_path: str, out_path: str = "source-prepped.png") -> None:
    src_bytes = Path(src_path).read_bytes()
    cutout_bytes = remove(src_bytes)
    cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

    # Crop to the subject so the ASCII grid isn't mostly blank, then pad the
    # short side to roughly square (the char grid is near 1:1 once glyph
    # aspect is accounted for).
    bbox = cutout.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        cutout = cutout.crop(bbox)
    w, h = cutout.size
    side = max(w, h)
    squared = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    squared.paste(cutout, ((side - w) // 2, (side - h) // 2))
    cutout = squared

    # Composite the transparent cutout onto pure white.
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # CLAHE on the luminance channel to recover shadow/highlight detail.
    bgr = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    Image.fromarray(gray).save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python prep_photo.py <source-photo.jpg> [out.png]")
        sys.exit(1)
    prep(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png")
