"""Turn the supplied catalogue photography into product tiles in static/img/products/.

Run `python tools/prepare_product_photos.py` after adding photography.

The catalogue import left ten manufacturer photos in `images/`, filed under the short
slugs of the duplicate entries that no longer exist. This maps each one back onto its
live product, normalises it to a 16:10 studio tile and writes `static/img/products/
{slug}.webp`, which `Product.image_src` prefers over the drawn schematic plate.

Only plain studio shots qualify: a shot whose surround is not near-white or transparent
(promotional artwork with a coloured frame) stays on its plate rather than putting a
coloured block into a white card. The originals are never modified.

Rights: this photography is third-party material with no reuse licence established -
see the note in README.md. It is bundled for the draft, not cleared for publication.
"""

import os

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "images")
OUT = os.path.join(ROOT, "static", "img", "products")

# Catalogue file -> live product slug. Checked against catalog.json, name by name.
PHOTOS = {
    "primacy.png": "evolis-primacy-2",
    "quantum.png": "evolis-quantum",
    "zenius-2.jpg": "evolis-zenius-2",
    "ribbon.jpg": "evolis-ymcko-ribbons",
    "cards.jpg": "blank-pvc-cards",
    "sigma.jpg": "idemia-sigma-family",
    "visionpass.jpg": "idemia-visionpass",
    "minmoe.jpg": "hikvision-minmoe",
    "walkthrough.jpg": "walkthrough-detectors",
    "zk-d1090.jpg": "zkteco-zk-d1090",
}

TILE = (960, 600)
PAD = 0.07
WHITE = (255, 255, 255)
NEAR_WHITE = 244


def flatten(im):
    """Composite anything with an alpha channel onto white."""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        ground = Image.new("RGBA", im.size, WHITE + (255,))
        return Image.alpha_composite(ground, im).convert("RGB")
    return im.convert("RGB")


def plain_surrounds(im):
    """True when the frame of the shot is white or transparent, not branded artwork."""
    rgb = flatten(im)
    w, h = rgb.size
    probe = [(2, 2), (w // 2, 2), (w - 3, 2), (2, h // 2), (w - 3, h // 2), (2, h - 3), (w // 2, h - 3), (w - 3, h - 3)]
    if im.mode == "RGBA":
        alpha = im.getchannel("A")
        if all(alpha.getpixel(xy) < 12 for xy in probe):
            return True
    return all(min(rgb.getpixel(xy)) >= NEAR_WHITE for xy in probe)


def tile(im):
    """Trim the white margin, then centre the subject on a 16:10 white tile.

    Returns the tile and the subject's own bounding box, so a caller can judge how much
    detail there was to work with. Tall thin products (an arch, a pole) are supposed to
    leave white at the sides: the gate is the subject's longest edge, never its short one.
    """
    rgb = flatten(im)
    # a pixel belongs to the subject when even its palest channel is off-white, so a
    # light grey product is not trimmed away the way a luminance mask would trim it
    inverted = [ImageChops.invert(channel) for channel in rgb.split()]
    palest = ImageChops.lighter(ImageChops.lighter(*inverted[:2]), inverted[2]) if len(inverted) > 2 else ImageChops.lighter(*inverted)
    mask = palest.point(lambda v: 255 if v > 255 - NEAR_WHITE else 0)
    box = mask.getbbox()
    if box:
        rgb = rgb.crop(box)
    subject = max(rgb.width, rgb.height)
    limit = (round(TILE[0] * (1 - PAD)), round(TILE[1] * (1 - PAD)))
    # small catalogue crops are allowed to grow a little, but not far enough to blur
    scale = min(limit[0] / rgb.width, limit[1] / rgb.height, 1.35)
    size = (max(1, round(rgb.width * scale)), max(1, round(rgb.height * scale)))
    rgb = rgb.resize(size, Image.LANCZOS)
    out = Image.new("RGB", TILE, WHITE)
    out.paste(rgb, (round((TILE[0] - size[0]) / 2), round((TILE[1] - size[1]) / 2)))
    return out, subject


def main():
    os.makedirs(OUT, exist_ok=True)
    written, skipped = [], []
    for filename, slug in sorted(PHOTOS.items()):
        path = os.path.join(SOURCE, filename)
        if not os.path.exists(path):
            skipped.append((slug, "no source file"))
            continue
        with Image.open(path) as im:
            if not plain_surrounds(im):
                skipped.append((slug, "branded or coloured surround - kept the plate"))
                continue
            art, subject = tile(im)
            if subject < 340:
                skipped.append((slug, f"subject only {subject}px across at source"))
                continue
            target = os.path.join(OUT, f"{slug}.webp")
            art.save(target, "WEBP", quality=84, method=6)
            written.append((slug, f"{TILE[0]}x{TILE[1]} from a {subject}px subject"))
    for slug, note in written:
        print(f"  tile   {slug:28} {note}")
    for slug, note in skipped:
        print(f"  kept plate {slug:26} ({note})")
    print(f"wrote {len(written)} photo tiles, {len(skipped)} left on their plate")


if __name__ == "__main__":
    main()
