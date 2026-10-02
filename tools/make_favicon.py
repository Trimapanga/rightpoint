"""Rebuild the tab icons from `static/img/logo.png`.

Run with the project interpreter: `python tools/make_favicon.py`

The logo is a 326x200 lockup: a ring, the letters RPS, and a "Right Point
Solutions" wordmark underneath. Scaled into a 16px tab the wordmark is mush and
the transparent surround turns black on iOS, so the icon keeps the ring-and-RPS
mark on a white plate. The wordmark is removed by blanking the corner it lives
in - that rectangle is chosen against the artwork, not guessed: the lowest
letter of RPS ends at y=131 and the ring's lower green sweep ends at x=186, so
clearing from (185, 133) outwards takes the wordmark and nothing else.
"""
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO = BASE_DIR / "static" / "img" / "logo.png"
OUT = BASE_DIR / "static" / "img"

# Top-left of the corner the wordmark occupies, clear of RPS and the lower sweep.
WORDMARK_CORNER = (185, 133)

# size, filename, plate corner radius as a share of the side (0 for iOS, which masks itself)
PLATES = [(32, "favicon-32.png", 0.16), (192, "favicon-192.png", 0.12),
          (180, "apple-touch-icon.png", 0.0)]


def mark():
    logo = Image.open(LOGO).convert("RGBA")
    blank = Image.new("RGBA", (logo.width - WORDMARK_CORNER[0],
                               logo.height - WORDMARK_CORNER[1]), (0, 0, 0, 0))
    logo.paste(blank, WORDMARK_CORNER)
    return logo.crop(logo.split()[3].getbbox())


def plate(glyph, size, radius):
    side = int(round(max(glyph.size) * 1.16))
    art = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    if radius:
        card = Image.new("L", (side, side), 0)
        ImageDraw.Draw(card).rounded_rectangle(
            [0, 0, side - 1, side - 1], radius=int(side * radius), fill=255)
    else:
        card = Image.new("L", (side, side), 255)
    art.paste((255, 255, 255, 255), (0, 0), card)
    art.paste(glyph, ((side - glyph.width) // 2, (side - glyph.height) // 2), glyph)
    return art.resize((size, size), Image.LANCZOS)


def main():
    glyph = mark()
    print(f"mark {glyph.width}x{glyph.height} from {LOGO.name}")
    # The mark on transparency too: the admin login card is a white surface, so a
    # plated favicon would read as a visible square sitting on top of it.
    glyph.save(OUT / "mark.png", optimize=True)
    for size, name, radius in PLATES:
        out = OUT / name
        plate(glyph, size, radius).save(out)
        print(f"wrote {out.relative_to(BASE_DIR)} ({out.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
