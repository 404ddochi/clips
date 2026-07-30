#!/usr/bin/env python3
"""Generate CLIPS favicon / PWA icon PNG and ICO assets (dev tool).

Requires Pillow (not a runtime dependency):

    .venv/bin/pip install pillow
    .venv/bin/python scripts/render_app_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "app" / "static" / "icons"

BG = (8, 11, 18, 255)  # --color-bg-primary / dark theme-color
GOLD = (198, 161, 91, 255)
GOLD_SOFT = (223, 189, 115, 255)
GOLD_CORE = (255, 248, 234, 255)


def _draw_mark(
    size: int,
    *,
    with_background: bool,
    maskable: bool = False,
) -> Image.Image:
    """Eclipse ring mark. Maskable keeps the glyph inside the center safe zone."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if with_background:
        if maskable:
            draw.rectangle((0, 0, size - 1, size - 1), fill=BG)
        else:
            radius = max(2, round(size * 0.18))
            draw.rounded_rectangle(
                (0, 0, size - 1, size - 1),
                radius=radius,
                fill=BG,
            )

    pad_ratio = 0.22 if maskable else 0.16
    pad = size * pad_ratio
    cx = cy = size / 2.0
    outer_r = (size / 2.0) - pad
    ring_w = max(2, round(size * 0.09))

    # C-cut outer ring
    bbox = (
        cx - outer_r,
        cy - outer_r,
        cx + outer_r,
        cy + outer_r,
    )
    draw.arc(bbox, start=38, end=322, fill=GOLD, width=ring_w)

    # Inner ring
    inner_r = outer_r * 0.58
    inner_w = max(1, round(size * 0.035))
    ib = (
        cx - inner_r,
        cy - inner_r,
        cx + inner_r,
        cy + inner_r,
    )
    draw.ellipse(ib, outline=GOLD_SOFT, width=inner_w)

    # Core
    core_r = max(1.5, outer_r * 0.24)
    hi_r = max(1.0, core_r * 0.45)
    draw.ellipse(
        (cx - core_r, cy - core_r, cx + core_r, cy + core_r),
        fill=GOLD_SOFT,
    )
    draw.ellipse(
        (cx - hi_r, cy - hi_r, cx + hi_r, cy + hi_r),
        fill=GOLD_CORE,
    )
    return img


def _save_png(img: Image.Image, path: Path, *, keep_alpha: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if keep_alpha:
        img.save(path, format="PNG", optimize=True)
    else:
        img.convert("RGB").save(path, format="PNG", optimize=True)
    print(f"wrote {path.relative_to(ROOT)} ({img.size[0]}x{img.size[1]}, {path.stat().st_size}B)")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    assets: list[tuple[str, Image.Image, bool]] = [
        ("favicon-16x16.png", _draw_mark(16, with_background=True), False),
        ("favicon-32x32.png", _draw_mark(32, with_background=True), False),
        ("apple-touch-icon.png", _draw_mark(180, with_background=True), False),
        ("android-chrome-192x192.png", _draw_mark(192, with_background=True), False),
        ("android-chrome-512x512.png", _draw_mark(512, with_background=True), False),
        ("maskable-icon-512x512.png", _draw_mark(512, with_background=True, maskable=True), False),
    ]
    for name, image, keep_alpha in assets:
        _save_png(image, OUT_DIR / name, keep_alpha=keep_alpha)

    ico_path = OUT_DIR / "favicon.ico"
    icon32 = _draw_mark(32, with_background=True).convert("RGBA")
    icon32.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32)])
    print(f"wrote {ico_path.relative_to(ROOT)} ({ico_path.stat().st_size}B)")


if __name__ == "__main__":
    main()
