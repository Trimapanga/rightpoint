# Product photography still needed

Drop a manufacturer media-kit shot here named after the product slug - `images/
hikvision-colorvu.jpg` - then run `python tools/prepare_product_photos.py`. Each accepted
file becomes a 960x600 studio tile at `static/img/products/<slug>.webp`, which the product
card prefers over its drawn plate. `--check` prints this list at any time.

What a tile has to be:

- the actual equipment the card names, shot straight, on white or transparent
- at least ~340px across on its longest edge, or it enlarges into a blur
- not a datasheet page, a branded promo graphic, or a concept illustration
- for a software product (`morphomanager`) a clean interface screenshot is the honest
  depiction - there is no device to photograph

A file whose name is not a product slug is reported and ignored, so a typo cannot quietly
put the wrong device on a card. The studio gate rejects a coloured surround, and
`products.tests.ProductArtworkTests.test_only_checked_photography_is_published` pins the
published set: a new tile also needs a line in that list, written after looking at the
picture rather than trusting its filename.

## Rejected - do not re-add these as they are

| source | what it actually is |
| --- | --- |
| `images/quantum.png` | a FAAC Quantum sliding barrier. The Evolis Quantum is a card printer. |
| `images/cards.jpg` | an IDStore.us promo graphic: reseller logo top, IDST fingerprint watermark across the middle. |
| `static/img/products/morphomanager.jpg` | a stock isometric "software team" illustration. No device in it. |

The first two produced tiles that were live for a while; both are parked in
`images/rejected/`. `evolis-quantum` and `blank-pvc-cards` are back on their drawn plates
until a real printer shot and a clean card shot arrive.

## Waiting (20)

- `images/entrust-sigma-ds2.jpg` - Entrust Sigma DS2 (Entrust) - secure dual-sided issuance
- `images/entrust-sigma-ds3.jpg` - Entrust Sigma DS3 (Entrust) - programme-scale issuance
- `images/blank-pvc-cards.jpg` - Blank PVC cards (Evolis) - card stock
- `images/evolis-badgy-2.jpg` - Evolis Badgy 2 (Evolis) - entry-level card issuance
- `images/evolis-quantum.jpg` - Evolis Quantum (Evolis) - high-volume card issuance
- `images/evolis-zenius.jpg` - Evolis Zenius (Evolis) - re-transfer desktop issuance
- `images/evolis-accessories.jpg` - Evolis accessories (Evolis) - keep your issuance ready
- `images/evolis-cleaning-kits.jpg` - Evolis cleaning kits (Evolis) - printer maintenance
- `images/hikvision-colorvu.jpg` - Hikvision ColorVu (Hikvision) - full colour around the clock
- `images/hikvision-ds-k1t671.jpg` - Hikvision DS-K1T671 Pro Face Access Terminal (Hikvision) - pro face access terminal
- `images/hikvision-darkfighter.jpg` - Hikvision DarkFighter (Hikvision) - detail in very low light
- `images/hikvision-minmoe.jpg` - Hikvision MinMoe (Hikvision) - multi-modal terminals
- `images/hikvision-turbo-hd.jpg` - Hikvision Turbo HD (Hikvision) - hd video over existing coax
- `images/hikvision-card-readers.jpg` - Hikvision card readers (Hikvision) - credential readers
- `images/hikvision-nvr.jpg` - Hikvision network video recorders (Hikvision) - recording and review
- `images/idemia-visionpass.jpg` - IDEMIA VisionPass (IDEMIA) - face-first entry
- `images/morphomanager.jpg` - MorphoManager (IDEMIA) - centralised management
- `images/zkteco-handheld-metal-detectors.jpg` - Handheld metal detectors (ZKTeco) - secondary screening
- `images/zkteco-f18.jpg` - ZKTeco F18 (ZKTeco) - standalone fingerprint access
- `images/zkteco-megaface.jpg` - ZKTeco MegaFace series (ZKTeco) - high-accuracy face verification

## Tiled and checked (6)

`evolis-primacy-2`, `evolis-ymcko-ribbons`, `evolis-zenius-2`, `idemia-sigma-family`, `walkthrough-detectors`, `zkteco-zk-d1090`

Two sources are present but refused by the studio gate: `minmoe.jpg` (Hikvision MinMoe)
and `visionpass.jpg` (IDEMIA VisionPass) are promo artwork on a coloured surround. Replace
either with a straight shot on white to unlock that card.

## Rights

Distributor media kits are licensed to resellers, which is why they are the expected source.
The eight files already here came from the 2026-09-30 catalogue import and have no
established reuse licence - see the catalogue-import note in `README.project.md`.
