"""Turn product photography into tiles in static/img/products/.

Drop a manufacturer media-kit shot into `images/` named after the product slug -
`images/hikvision-colorvu.jpg`, `images/evolis-zenius.png` and so on - then run
`python tools/prepare_product_photos.py`. `--check` lists the slugs still waiting
for a photograph. A slug is recognised when a drawn plate already exists for it in
`static/img/products/`, which is what keeps a typo'd filename from inventing a product.

The 2026-09-30 catalogue import left ten manufacturer photos under the short slugs of
duplicate entries that no longer exist, so those filenames are mapped by hand below.
Each one normalises to a 16:10 studio tile at `static/img/products/{slug}.webp`, which
`Product.image_src` prefers over the drawn schematic plate.

Only plain studio shots qualify: a shot whose surround is not near-white or transparent
(promotional artwork with a coloured frame) stays on its plate rather than putting a
coloured block into a white card. A subject narrower than 340px at source is refused
too, because it would have to be enlarged into a blur. Screenshots and concept
illustrations pass both gates, so they are the uploader's judgement call: this is a
catalogue of equipment, and the tile has to show that equipment. The originals are
never modified.

Rights: distributor media kits are licensed to resellers, which is why they are the
expected source. The ten import leftovers have no reuse licence established - see the
note in README.project.md - and are bundled for the draft, not cleared for publication.
"""

import argparse
import os

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "images")
OUT = os.path.join(ROOT, "static", "img", "products")

SOURCE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

# Catalogue import file -> live product slug. Checked against catalog.json, name by name,
# and then checked again against the photograph itself: two of the ten are not what the
# filename claimed. `quantum.png` is a FAAC Quantum sliding barrier, not an Evolis
# Quantum card printer, and `cards.jpg` is an IDStore.us promo graphic carrying the
# reseller's logo and a fingerprint watermark. Both are dropped from the map, so those
# two cards keep their drawn plate; the tiles they produced are parked in
# `images/rejected/` rather than deleted, and `products.tests` pins the published set.
LEGACY_PHOTOS = {
    "primacy.png": "evolis-primacy-2",
    "zenius-2.jpg": "evolis-zenius-2",
    "ribbon.jpg": "evolis-ymcko-ribbons",
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


def plate_slugs():
    """The slugs that ship a drawn plate, which is the list of products that exist."""
    return {os.path.splitext(name)[0] for name in os.listdir(OUT) if name.endswith(".svg")}


def collect_sources(live):
    """Return ({slug: path}, [notes]) for the photographs `images/` currently offers.

    A file is used when it is named for a live product, or named in the legacy map -
    anything else is reported rather than guessed at, because a misfiled photo is the
    one failure mode that puts the wrong product on a card.
    """
    pairs, notes = {}, []
    if not os.path.isdir(SOURCE):
        return pairs, [f"{SOURCE} does not exist"]
    for name in sorted(os.listdir(SOURCE)):
        path = os.path.join(SOURCE, name)
        stem, extension = os.path.splitext(name)
        if not os.path.isfile(path) or extension.lower() not in SOURCE_EXTENSIONS:
            continue
        slug = LEGACY_PHOTOS.get(name) or (stem if stem in live else None)
        if slug is None:
            notes.append(f"ignored    {name} (no product uses that slug)")
        elif slug in pairs:
            notes.append(f"ignored    {name} ({slug} already has a source)")
        else:
            pairs[slug] = path
    return pairs, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="List the products still waiting for a photograph.")
    options = parser.parse_args()

    live = plate_slugs()
    pairs, notes = collect_sources(live)
    tiled = {os.path.splitext(name)[0] for name in os.listdir(OUT) if name.endswith(".webp")}
    waiting = sorted(live - tiled)

    if options.check:
        for slug in waiting:
            if slug in pairs:
                print(f"  source present  {os.path.basename(pairs[slug])} -> {slug} (run the tool; the studio gate decides)")
            else:
                print(f"  needs a photo   images/{slug}.jpg")
        for note in notes:
            print(" " + note)
        print(f"{len(live) - len(waiting)} of {len(live)} products have a photo tile; {len(waiting)} on drawn plates")
        return

    written, skipped = [], []
    for slug in sorted(pairs):
        path = pairs[slug]
        with Image.open(path) as im:
            if not plain_surrounds(im):
                skipped.append((slug, "branded or coloured surround - kept the plate"))
                continue
            art, subject = tile(im)
            if subject < 340:
                skipped.append((slug, f"subject only {subject}px across at source"))
                continue
            art.save(os.path.join(OUT, f"{slug}.webp"), "WEBP", quality=84, method=6)
            written.append((slug, f"{TILE[0]}x{TILE[1]} from a {subject}px subject in {os.path.basename(path)}"))
    for slug, note in written:
        print(f"  tile   {slug:34} {note}")
    for slug, note in skipped:
        print(f"  kept plate {slug:32} ({note})")
    for note in notes:
        print(" " + note)
    still = [slug for slug in waiting if slug not in {written_slug for written_slug, _ in written}]
    print(f"wrote {len(written)} tiles; {len(still)} products are still on their drawn plate")


if __name__ == "__main__":
    main()
