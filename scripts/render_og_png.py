#!/usr/bin/env python3
"""Render app/static/images/og/clips-og.png from the OG layout (dev asset tool).

Requires Pillow (not a runtime dependency). Example:

    .venv/bin/pip install pillow
    .venv/bin/python scripts/render_og_png.py

Prefer SVG→PNG with librsvg when available:

    rsvg-convert -w 1200 -h 630 app/static/images/og/clips-og.svg \\
      -o app/static/images/og/clips-og.png
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app/static/images/og/clips-og.png"
W, H = 1200, 630
FONT_TTC = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
FONT_TTF = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if FONT_TTC.exists():
        indices = (8, 6, 7, 1, 0) if bold else (0, 1, 2)
        for index in indices:
            try:
                return ImageFont.truetype(str(FONT_TTC), size=size, index=index)
            except OSError:
                continue
    if FONT_TTF.exists():
        return ImageFont.truetype(str(FONT_TTF), size=size)
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), "#080b12").convert("RGBA")

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((650, 40, 1180, 560), fill=(198, 161, 91, 48))
    g.ellipse((-80, -120, 520, 360), fill=(70, 110, 180, 36))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(48)))

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 28):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 9))
    for y in range(0, H, 28):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 9))
    img = Image.alpha_composite(img, grid)

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(veil).rectangle((0, 0, 720, H), fill=(8, 11, 18, 72))
    img = Image.alpha_composite(img, veil)

    cx, cy = 840, 315
    ecl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    blob = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(blob).ellipse(
        (cx - 210, cy - 210, cx + 210, cy + 210),
        fill=(198, 161, 91, 28),
    )
    ecl = Image.alpha_composite(ecl, blob.filter(ImageFilter.GaussianBlur(28)))
    ed = ImageDraw.Draw(ecl)
    for radius, opacity, width in ((236, 140, 2), (214, 72, 1), (192, 88, 1)):
        ed.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=(198, 161, 91, opacity),
            width=width,
        )
    ed.ellipse(
        (cx - 148, cy - 148, cx + 148, cy + 148),
        fill=(20, 26, 40, 255),
        outline=(198, 161, 91, 90),
        width=2,
    )
    ed.ellipse((cx - 56, cy - 56, cx + 56, cy + 56), fill=(198, 161, 91, 26))
    ed.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(223, 189, 115, 90))
    ed.arc((cx - 106, cy - 106, cx + 106, cy + 106), 200, 300, fill=(198, 161, 91, 150), width=2)
    ed.arc((cx - 106, cy - 106, cx + 106, cy + 106), 320, 30, fill=(198, 161, 91, 90), width=2)
    ed.line([(cx - 132, cy), (cx + 132, cy)], fill=(198, 161, 91, 40), width=1)
    ed.line([(cx, cy - 132), (cx, cy + 132)], fill=(198, 161, 91, 30), width=1)
    for px, py, radius, color in (
        (cx + 118, cy - 126, 3, (223, 189, 115, 220)),
        (cx - 146, cy - 48, 2, (223, 189, 115, 140)),
        (cx + 156, cy + 72, 3, (198, 161, 91, 180)),
        (cx - 98, cy + 138, 2, (223, 189, 115, 110)),
        (cx + 48, cy - 168, 2, (255, 248, 234, 140)),
    ):
        ed.ellipse((px - radius, py - radius, px + radius, py + radius), fill=color)
    img = Image.alpha_composite(img, ecl)

    draw = ImageDraw.Draw(img)
    draw.text((80, 104), "ECLIPSE: THE AWAKENING", fill=(198, 161, 91), font=_font(22, bold=True))
    draw.text((80, 148), "CLIPS", fill=(255, 248, 234), font=_font(108, bold=True))
    draw.text((80, 268), "이클립스: 더 어웨이크닝", fill=(244, 241, 232), font=_font(40, bold=True))
    draw.text((80, 324), "정보 플랫폼", fill=(169, 173, 186), font=_font(30, bold=True))
    draw.text((80, 406), "소식, 클래스, 아이템, 보스, 지도와", fill=(169, 173, 186), font=_font(24))
    draw.text(
        (80, 442),
        "게임에 필요한 정보를 한곳에서 확인하세요.",
        fill=(169, 173, 186),
        font=_font(24),
    )
    draw.text((80, 524), "playclips.kr", fill=(198, 161, 91), font=_font(22, bold=True))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT, format="PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
