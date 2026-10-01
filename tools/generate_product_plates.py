"""Redraw the bundled product plates in static/img/products/.

Run `python tools/generate_product_plates.py` after adding a product: every slug needs
a plate or its card falls back to the brand monogram.

Every plate is a 320x200 schematic elevation on a transparent ground: it sits on
top of the CSS gradient card artwork, so no background is painted here.
"""

import math
import os

INK = "#0d1b20"
MID = "#5b7480"
PALE = "#c3d2d8"
# Bodies, recessed panels and optics are gradients, not flats: the plates sit on a
# pale CSS ground, so tonal separation is what reads as depth.
BODY = "url(#b)"
SHADE = "url(#h)"
GLASS = "url(#g)"
DARK = "url(#o)"
BLUE = "#023aaa"
GREEN = "#2b990b"

# Card media renders these at roughly 0.6 of the 320px viewBox, so every stroke
# is scaled up once here rather than at each call site.
WEIGHT = 1.2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "img", "products")


def _w(stroke_width):
    return None if stroke_width is None else round(stroke_width * WEIGHT, 2)


class D:
    def __init__(self):
        self.parts = []

    def el(self, tag, attrs, close=False):
        bits = []
        for key, value in attrs.items():
            if value is None:
                continue
            bits.append(f'{key}="{value}"')
        joined = " ".join(bits)
        if close:
            self.parts.append(f"<{tag} {joined}/>")
        else:
            self.parts.append(f"<{tag} {joined}></{tag}>")

    def rect(self, x, y, w, h, r=0, fill=BODY, stroke=INK, sw=2, dash=None):
        self.el(
            "rect",
            {
                "x": x, "y": y, "width": w, "height": h, "rx": r or None,
                "fill": fill, "stroke": stroke, "stroke-width": _w(sw),
                "stroke-dasharray": dash,
            },
            close=True,
        )

    def path(self, d, stroke=INK, sw=2, fill="none", dash=None, opacity=None):
        self.el(
            "path",
            {
                "d": d, "stroke": stroke, "stroke-width": _w(sw), "fill": fill,
                "stroke-dasharray": dash, "opacity": opacity,
            },
            close=True,
        )

    def line(self, x1, y1, x2, y2, stroke=MID, sw=1.5):
        self.el(
            "line",
            {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": stroke, "stroke-width": _w(sw)},
            close=True,
        )

    def circle(self, cx, cy, r, fill=None, stroke=INK, sw=2, dash=None, opacity=None):
        self.el(
            "circle",
            {
                "cx": cx, "cy": cy, "r": r, "fill": fill, "stroke": stroke,
                "stroke-width": _w(sw), "stroke-dasharray": dash, "opacity": opacity,
            },
            close=True,
        )

    def ellipse(self, cx, cy, rx, ry, fill=BODY, stroke=INK, sw=2):
        self.el(
            "ellipse",
            {"cx": cx, "cy": cy, "rx": rx, "ry": ry, "fill": fill, "stroke": stroke, "stroke-width": _w(sw)},
            close=True,
        )

    def group(self, inner, transform):
        self.parts.append(f'<g transform="{transform}">')
        inner()
        self.parts.append("</g>")

    def ground(self, cx=160, cy=168, rx=104, ry=9):
        self.ellipse(cx, cy, rx, ry, fill=INK, stroke=None, sw=None)
        self.parts[-1] = self.parts[-1].replace('fill="#0d1b20"', 'fill="#0d1b20" opacity="0.07"', 1)

    def render(self, title):
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" width="320" height="200" role="img" aria-label="{title}">\n'
            f"  <title>{title}</title>\n" + DEFS +
            '  <g fill="none" stroke-linecap="round" stroke-linejoin="round" filter="url(#lift)">\n'
            + "\n".join("    " + p for p in self.parts)
            + "\n  </g>\n</svg>\n"
        )


GRADIENTS = (
    ('b', "linear", {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
     ((0, "#ffffff"), (0.5, "#f5f9fb"), (1, "#dde8ec"))),
    ('h', "linear", {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
     ((0, "#eff5f7"), (1, "#d0dde3"))),
    ('g', "linear", {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
     ((0, "#e9f2f5"), (1, "#c0d6de"))),
    ('o', "radial", {"cx": 0.42, "cy": 0.36, "r": 0.74},
     ((0, "#3c6879"), (1, "#11242d"))),
)

DEFS = "  <defs>\n" + "".join(
    '    <{0}Gradient id="{1}" {2}>{3}</{0}Gradient>\n'.format(
        kind,
        gid,
        " ".join(f'{k}="{v}"' for k, v in attrs.items()),
        "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops),
    )
    for gid, kind, attrs, stops in GRADIENTS
) + (
    '    <filter id="lift" x="-16%" y="-16%" width="132%" height="132%">'
    '<feDropShadow dx="0" dy="2.5" stdDeviation="3" flood-color="#0d1b20" flood-opacity=".18"/></filter>\n'
    "  </defs>\n"
)


# --------------------------------------------------------------------------- shapes


def printer_hopper(d, *, small=False, dual=False, feed=False):
    """Evolis-style desktop card printer: top hopper, ribbon window, front screen."""
    d.ground(cy=170, rx=100)
    d.path("M108,74 L120,46 L200,46 L212,74", fill=SHADE)
    d.rect(130, 52, 60 if not dual else 74, 15, 3, fill=BODY, sw=1.5)
    d.line(134, 60, 184, 60, PALE, 1.25)
    d.rect(74, 74, 172, 74, 12)
    d.rect(88, 88, 76, 44, 6, fill=SHADE, sw=1.75)
    d.rect(97, 96, 58, 28, 3, fill=GLASS, stroke=MID, sw=1.25)
    d.circle(112, 110, 9, stroke=MID, sw=1.25)
    d.circle(140, 110, 9, stroke=MID, sw=1.25)
    d.circle(112, 110, 2.5, fill=MID, stroke=None)
    d.circle(140, 110, 2.5, fill=MID, stroke=None)
    if small:
        d.rect(178, 92, 52, 26, 5, fill=GLASS, sw=1.5)
        d.line(186, 101, 220, 101, MID, 1.5)
        d.line(186, 109, 206, 109, PALE, 1.5)
    else:
        d.rect(176, 86, 56, 34, 6, fill=GLASS, sw=1.75)
        d.line(184, 95, 222, 95, MID, 1.5)
        d.line(184, 103, 212, 103, PALE, 1.5)
        d.line(184, 111, 202, 111, PALE, 1.5)
        d.circle(224, 111, 3.5, fill=GREEN, stroke=None)
    d.rect(176, 126, 54, 6, 3, fill=PALE, stroke=None)
    if dual:
        d.rect(236, 126, 14, 6, 3, fill=PALE, stroke=None)
    cards = 2 if dual else 1
    for i in range(cards):
        shift = i * 11
        d.group(
            lambda: _card(d, 176 - shift, 134 - i * 4, 56, 34, sw=1.75 if i else 2),
            f"rotate(-7 204 150)",
        )
    if feed:
        # single-sheet manual slot across the front, one card stood up in it
        d.rect(90, 138, 70, 5, 2, fill=DARK, stroke=None)
        d.rect(96, 126, 58, 14, 3, fill=BODY, sw=1.5)
        d.line(102, 133, 148, 133, PALE, 1.5)
        d.line(102, 129, 140, 129, MID, 1.25)


def printer_volume(d):
    """Production-scale issuer: twin 500-card hoppers, control panel, duplex exit."""
    d.ground(cy=172, rx=116)
    d.rect(82, 44, 66, 42, 6, fill=SHADE)
    for i in range(4):
        d.line(90, 54 + i * 8, 140, 54 + i * 8, PALE, 1.5)
    d.rect(166, 56, 52, 30, 5, fill=SHADE)
    for i in range(3):
        d.line(174, 64 + i * 8, 210, 64 + i * 8, MID, 1.5)
    d.rect(70, 86, 176, 74, 12)
    d.line(70, 102, 246, 102, PALE, 1.5)
    d.rect(82, 110, 70, 40, 6, fill=GLASS, sw=1.75)
    d.line(90, 120, 144, 120, MID, 1.5)
    d.line(90, 128, 130, 128, PALE, 1.5)
    d.rect(90, 136, 20, 6, 3, fill=GREEN, stroke=None)
    d.rect(116, 136, 20, 6, 3, fill=BLUE, stroke=None)
    for i in range(2):
        shift = i * 10
        d.group(
            lambda: _card(d, 186 - shift, 112 - i * 4, 52, 32, sw=1.75 if not i else 1.5),
            "rotate(-7 212 128)",
        )
    for fx in (84, 208):
        d.rect(fx, 160, 24, 8, 3, fill=SHADE, stroke=None)


def _card(d, x, y, w, h, sw=2):
    d.rect(x, y, w, h, 4, fill=BODY, sw=sw)
    d.rect(x + 6, y + 7, 13, 11, 2, fill=None, stroke=MID, sw=1.25)
    d.line(x + 24, y + 10, x + w - 8, y + 10, PALE, 1.5)
    d.line(x + 24, y + 16, x + w - 16, y + 16, PALE, 1.5)
    d.line(x + 6, y + h - 9, x + w - 6, y + h - 9, BLUE, 2.5)


def printer_slot(d, *, colour=False):
    """Entrust-style issuance printer: a low body with the card rising from the top slot."""
    d.ground(cy=168, rx=104)
    d.group(
        lambda: (
            d.rect(124, 30, 74, 48, 5, fill=BODY, sw=1.75),
            d.rect(132, 38, 17, 14, 2, fill=None, stroke=MID, sw=1.25),
            d.line(154, 42, 190, 42, PALE, 1.5),
            d.line(154, 49, 182, 49, PALE, 1.5),
            d.line(132, 66, 192, 66, BLUE if colour else GREEN, 2.5),
        ),
        "rotate(5 161 54)",
    )
    d.rect(96, 82, 128, 8, 4, fill=PALE, stroke=None)
    d.rect(84, 88, 152, 62, 10)
    d.line(84, 100, 236, 100, PALE, 1.5)
    d.rect(150, 104, 74, 36, 5, fill=GLASS, sw=1.75)
    if colour:
        d.line(158, 114, 210, 114, MID, 1.5)
        d.line(158, 122, 196, 122, PALE, 1.5)
        d.rect(158, 129, 20, 6, 3, fill=GREEN, stroke=None)
        d.rect(182, 129, 20, 6, 3, fill=BLUE, stroke=None)
    else:
        d.line(158, 114, 206, 114, MID, 1.5)
        for i in range(3):
            d.circle(166 + i * 20, 130, 3.5, stroke=MID, sw=1.25)
    for i in range(3):
        d.line(94 + i * 6, 118, 94 + i * 6, 138, PALE, 1.5)
    d.circle(110, 108, 3.5, fill=GREEN, stroke=None)


def ribbon(d):
    d.ground(cy=160, rx=96)
    d.rect(60, 70, 200, 62, 10)
    d.rect(54, 80, 10, 42, 4, fill=SHADE, sw=1.75)
    d.rect(256, 80, 10, 42, 4, fill=SHADE, sw=1.75)
    d.circle(104, 101, 22, fill=SHADE, sw=1.75)
    d.circle(216, 101, 22, fill=SHADE, sw=1.75)
    d.circle(104, 101, 16, stroke=MID, sw=1.25, dash="3 5")
    d.circle(216, 101, 16, stroke=MID, sw=1.25, dash="3 5")
    d.circle(104, 101, 7, stroke=MID, sw=1.5)
    d.circle(216, 101, 7, stroke=MID, sw=1.5)
    d.rect(126, 96, 68, 10, 2, fill=PALE, stroke=None)
    d.line(126, 96, 194, 96, MID, 1.25)
    d.line(126, 106, 194, 106, MID, 1.25)
    key = [(BLUE, None), (MID, None), (GREEN, None), (INK, None), (PALE, MID)]
    for i, (colour, outline) in enumerate(key):
        d.rect(112 + i * 20, 142, 16, 9, 2, fill=colour, stroke=outline, sw=1 if outline else None)


def cleaning_kit(d):
    d.ground(cy=174, rx=104)
    d.rect(52, 74, 138, 16, 8, sw=1.75)
    d.line(64, 82, 172, 82, PALE, 1.5)
    d.circle(204, 82, 17, fill=SHADE)
    d.circle(204, 82, 6, stroke=MID, sw=1.5)
    d.path("M188,74 A16,16 0 0 0 188,90", stroke=MID, sw=1.5)
    d.rect(58, 118, 96, 46, 8)
    d.circle(82, 141, 12, stroke=MID, sw=1.5)
    d.circle(130, 141, 12, stroke=MID, sw=1.5)
    d.line(94, 141, 118, 141, PALE, 1.5)
    d.rect(174, 126, 88, 32, 6, fill=SHADE, sw=1.75)
    d.line(184, 136, 252, 136, PALE, 1.5)
    d.line(184, 148, 232, 148, PALE, 1.5)


def card_stack(d):
    d.ground(cy=184, rx=94)
    for i in range(4):
        shade = SHADE if i < 3 else BODY
        d.rect(70 + i * 9, 122 - i * 17, 140, 58, 9, fill=shade, sw=2 if i == 3 else 1.75)
    x, y = 97, 71
    d.rect(x + 8, y + 9, 22, 18, 3, fill=None, stroke=MID, sw=1.5)
    d.line(x + 38, y + 13, x + 116, y + 13, PALE, 1.75)
    d.line(x + 38, y + 21, x + 96, y + 21, PALE, 1.75)
    d.rect(x + 8, y + 33, 20, 14, 3, fill=None, stroke=BLUE, sw=1.75)
    d.rect(x + 2, y + 47, 136, 7, 2, fill=PALE, stroke=None)


def accessories(d):
    d.ground(cy=164, rx=104)
    d.ellipse(84, 114, 33, 31)
    d.circle(84, 96, 6, stroke=INK, sw=2)
    for i, (half, rise) in enumerate(((8, 8), (14, 17))):
        d.path(f"M{84 - half},134 Q84,{134 - rise * 2} {84 + half},134",
               stroke=BLUE, sw=2, opacity=1 - i * 0.4)
    d.rect(126, 84, 64, 58, 14)
    d.circle(156, 82, 7, stroke=INK, sw=2)
    for i, colour in enumerate((BLUE, GREEN, MID)):
        d.circle(141 + i * 15, 108, 4.5, fill=colour, stroke=None)
    d.line(138, 126, 174, 126, PALE, 1.75)
    d.rect(198, 78, 70, 66, 9)
    d.rect(206, 88, 54, 46, 4, fill=GLASS, stroke=MID, sw=1.5)
    d.rect(222, 62, 24, 16, 5, fill=SHADE, sw=1.75)
    d.line(214, 108, 236, 108, PALE, 1.5)
    d.line(214, 116, 246, 116, PALE, 1.5)


def wall_terminal(d, *, cams=1, keypad=False, reader=False, wide=False):
    d.ground(cy=178, rx=92)
    w = 112 if wide else 80
    x = 104 if wide else 120
    d.rect(x - 34, 34, w + 68, 140, 12, fill=None, stroke=PALE, sw=1.5, dash="7 7")
    for bx in (x - 24, x + w + 24):
        d.circle(bx, 46, 2.6, fill=MID, stroke=None)
        d.circle(bx, 162, 2.6, fill=MID, stroke=None)
    d.rect(x - 16, 32, w + 32, 142, 12, fill=SHADE, stroke=MID, sw=1.5)
    for px_ in (x - 7, x + w + 7):
        for py_ in (46, 158):
            d.circle(px_, py_, 2.4, fill=None, stroke=MID, sw=1.25)
    d.rect(x, 24, w, 150, 16)
    d.rect(x + 18, 42, w - 36, 18, 7, fill=DARK, stroke=None, sw=None)
    d.circle(x + w / 2 - (10 if cams == 2 else 0), 51, 5, stroke=BLUE, sw=1.75)
    if cams == 2:
        d.circle(x + w / 2 + 10, 51, 5, stroke=PALE, sw=1.75)
    d.circle(x + w - 16, 34, 3, fill=GREEN, stroke=None)
    d.rect(x + 10, 70, w - 20, 46, 6, fill=GLASS, sw=1.75)
    cx = x + w / 2
    d.circle(cx, 88, 7, stroke=GREEN, sw=1.75)
    d.path(f"M{cx - 13},110 A13,13 0 0 1 {cx + 13},110", stroke=GREEN, sw=1.75)
    d.line(x + 16, 122, x + w - 16, 122, PALE, 1.5)
    if keypad:
        for row in range(4):
            for col in range(3):
                d.circle(cx - 18 + col * 18, 132 + row * 13, 3, fill=PALE, stroke=MID, sw=1)
    elif reader:
        d.rect(cx - 15, 132, 30, 28, 5, fill=None, stroke=BLUE, sw=1.75)
        for i, (half, rise) in enumerate(((4, 6), (8, 12), (12, 18))):
            d.path(f"M{cx - half},153 Q{cx},{153 - rise * 2} {cx + half},153",
                   stroke=BLUE, sw=1.4, opacity=0.85 - i * 0.12)
    else:
        d.rect(x + 16, 130, w - 32, 12, 6, fill=SHADE, stroke=MID, sw=1.25)
        for i in range(4):
            d.line(x + 22 + i * 12, 152, x + 22 + i * 12, 164, PALE, 2)
        for r in (30, 42):
            d.path(f"M{x + w},{118 - r * 0.5} A{r},{r} 0 0 1 {x + w},{118 + r * 0.5}",
                   stroke=BLUE, sw=1.5, dash="5 7", opacity=0.75 - (r - 30) / 60)


def reader_wedge(d):
    d.ground(cy=158, rx=90)
    d.path("M88,144 L232,144 L224,110 Q222,102 214,102 L106,102 Q98,102 96,110 Z", fill=BODY)
    d.line(102, 116, 218, 116, PALE, 1.5)
    d.line(100, 138, 220, 138, GREEN, 2.4)
    for i, (half, rise) in enumerate(((13, 12), (25, 24), (37, 36))):
        d.path(f"M{160 - half},96 Q160,{96 - rise * 2} {160 + half},96",
               stroke=BLUE, sw=2.4, opacity=1 - i * 0.3)
    d.path("M232,144 Q252,148 258,132 Q262,120 276,118", stroke=INK, sw=2)
    d.circle(160, 126, 3.5, fill=BLUE, stroke=None)


def console(d):
    d.ground(cy=186, rx=96)
    d.rect(66, 34, 188, 120, 12)
    d.rect(76, 44, 168, 100, 6, fill=GLASS, stroke=MID, sw=1.5)
    d.rect(76, 44, 36, 100, 6, fill=SHADE, stroke=MID, sw=1.5)
    for i in range(5):
        d.line(84, 60 + i * 16, 104, 60 + i * 16, PALE, 2)
    d.rect(124, 54, 56, 7, 3, fill=PALE, stroke=None)
    d.rect(124, 70, 40, 5, 2, fill=MID, stroke=None)
    for i, (h, colour) in enumerate(((22, BLUE), (38, GREEN), (30, MID))):
        d.rect(126 + i * 22, 134 - h, 14, h, 2, fill=colour, stroke=None)
    d.line(120, 134, 190, 134, INK, 1.75)
    d.circle(218, 84, 17, stroke=INK, sw=2)
    d.path("M218,67 A17,17 0 0 1 235,84", stroke=BLUE, sw=4)
    d.line(198, 114, 240, 114, PALE, 1.75)
    d.line(198, 122, 230, 122, PALE, 1.75)
    d.path("M142,154 L152,174 L168,174 L178,154", fill=SHADE)
    d.rect(124, 172, 72, 8, 4)


def handheld_wand(d):
    d.ground(cy=176, rx=58)
    d.rect(104, 28, 112, 62, 18)
    d.rect(118, 40, 84, 38, 12, fill=None, stroke=MID, sw=1.5)
    for i, colour in enumerate((GREEN, GREEN, BLUE, PALE, PALE)):
        d.circle(126 + i * 17, 84, 3.2, fill=colour, stroke=None)
    d.rect(146, 90, 28, 16, 4, fill=SHADE)
    d.rect(134, 104, 52, 64, 14)
    d.rect(142, 112, 36, 13, 3, fill=GLASS, stroke=MID, sw=1.25)
    d.rect(124, 128, 12, 20, 6, fill=SHADE, sw=1.75)
    for i in range(3):
        d.line(144, 138 + i * 8, 176, 138 + i * 8, PALE, 1.5)
    d.circle(186, 156, 7, stroke=INK, sw=2)


def walkthrough(d, *, zones=7, panel=False):
    # the console stands outside the arch, so the shadow has to reach it
    d.ground(cx=150 if panel else 160, cy=176, rx=120 if panel else 104)
    d.rect(66, 14, 188, 16, 8, fill=SHADE)
    for i, colour in enumerate((GREEN, BLUE, MID)):
        d.rect(94 + i * 62, 18, 22, 8, 3, fill=colour, stroke=None)
    d.rect(70, 30, 38, 142, 8)
    d.rect(212, 30, 38, 142, 8)
    gap = 108 / (zones - 1)
    height = round(gap * 0.66, 1)
    for i in range(zones):
        third = zones / 3
        colour = GREEN if i < third else BLUE if i < third * 2 else PALE
        y = 40 + i * gap
        d.rect(98, y, 7, height, 3, fill=colour, stroke=None)
        d.rect(215, y, 7, height, 3, fill=colour, stroke=None)
        d.line(80, y + height / 2, 92, y + height / 2, PALE, 1.5)
        d.line(228, y + height / 2, 240, y + height / 2, PALE, 1.5)
    d.path("M108,172 L212,172", stroke=MID, sw=1.75, dash="7 7")
    if panel:
        # side console: the count screen and keypad that stand beside one pillar
        d.rect(20, 68, 40, 56, 6)
        d.rect(26, 74, 28, 18, 4, fill=GLASS, sw=1.5)
        d.line(30, 80, 50, 80, MID, 1.5)
        d.line(30, 86, 44, 86, PALE, 1.5)
        for row in range(3):
            for col in range(3):
                d.circle(31 + col * 9, 100 + row * 8, 2, fill=PALE, stroke=MID, sw=1)
        for arm in (92, 108):
            d.path(f"M60,{arm} L70,{arm}", stroke=INK, sw=2.25)
        d.rect(26, 124, 28, 6, 3, fill=SHADE, stroke=None)


def bullet(d, *, ir=False, warm=False):
    d.ground(cy=168, rx=88)
    d.rect(150, 148, 62, 14, 5, fill=SHADE)
    d.circle(162, 155, 2.5, fill=MID, stroke=None)
    d.circle(200, 155, 2.5, fill=MID, stroke=None)
    d.rect(172, 122, 16, 28, 4, fill=SHADE)
    d.circle(180, 118, 10, fill=BODY, sw=2)
    d.rect(88, 84, 132, 44, 22)
    d.path("M96,84 Q92,72 108,72 L212,72", sw=2)
    d.circle(96, 106, 21, fill=GLASS)
    d.circle(96, 106, 12, fill=DARK, stroke=None, sw=None)
    d.circle(92, 102, 3.8, fill=BLUE, stroke=None)
    if warm:
        d.circle(96, 106, 17, stroke=GREEN, sw=1.5, dash="3 5")
    if ir:
        for i in range(8):
            ang = i * math.pi / 4
            d.circle(96 + 16.5 * math.cos(ang), 106 + 16.5 * math.sin(ang), 1.8, fill=MID, stroke=None)
    d.path("M220,106 Q244,106 250,124 Q254,136 268,138", sw=2)


def turret(d):
    d.ground(cy=176, rx=76)
    d.ellipse(160, 52, 62, 14, fill=SHADE)
    d.circle(118, 52, 2.5, fill=MID, stroke=None)
    d.circle(202, 52, 2.5, fill=MID, stroke=None)
    d.rect(124, 56, 72, 46, 10)
    d.line(132, 74, 188, 74, PALE, 1.5)
    d.circle(160, 118, 40, fill=GLASS)
    d.circle(160, 118, 20, fill=DARK, stroke=None, sw=None)
    d.circle(160, 118, 9, stroke=PALE, sw=1.5)
    d.circle(153, 111, 4, fill=BLUE, stroke=None)
    d.path("M124,118 A36,36 0 0 0 196,118", stroke=MID, sw=1.25, dash="4 6")
    for i in range(4):
        d.circle(160 + 30 * math.cos(i * math.pi / 2 + math.pi / 4), 118 + 30 * math.sin(i * math.pi / 2 + math.pi / 4), 2.2, fill=MID, stroke=None)


def nvr(d):
    d.ground(cy=170, rx=112)
    d.rect(46, 42, 12, 124, 4, fill=SHADE)
    d.rect(262, 42, 12, 124, 4, fill=SHADE)
    for cy in (44, 112):
        d.rect(58, cy, 204, 54, 8)
        d.rect(70, cy + 12, 46, 30, 4, fill=GLASS, stroke=MID, sw=1.5)
        d.line(76, cy + 27, 110, cy + 27, PALE, 1.5)
        for i, colour in enumerate((GREEN, BLUE, MID)):
            d.circle(130 + i * 13, cy + 20, 3.2, fill=colour, stroke=None)
        d.rect(126, cy + 32, 46, 8, 4, fill=PALE, stroke=None)
        for group in range(3):
            for i in range(4):
                d.line(188 + group * 24 + i * 6, cy + 12, 188 + group * 24 + i * 6, cy + 40, PALE, 1.5)
    for ear in (52, 268):
        for ey in (56, 90, 120, 154):
            d.circle(ear, ey, 2.4, fill=MID, stroke=None)




PLATES = {}


def plate(slug, title, draw):
    PLATES[slug] = (title, draw)


plate("evolis-primacy-2", "Evolis Primacy 2 dual-slot card printer schematic", lambda d: printer_hopper(d))
plate("evolis-badgy-2", "Evolis Badgy 2 desktop card printer schematic", lambda d: printer_hopper(d, small=True))
plate("evolis-zenius", "Evolis Zenius dual module card printer schematic", lambda d: printer_hopper(d, dual=True))
plate("evolis-zenius-2", "Evolis Zenius 2 compact single-sided card printer schematic",
      lambda d: printer_hopper(d, small=True, feed=True))
plate("evolis-quantum", "Evolis Quantum high-volume card printer schematic", printer_volume)
plate("hikvision-ds-k1t671", "Hikvision DS-K1T671 Pro face recognition terminal schematic",
      lambda d: wall_terminal(d, wide=True, keypad=True))
plate("zkteco-zk-d1090", "ZKTeco ZK-D1090 walk-through metal detector with side console schematic",
      lambda d: walkthrough(d, zones=9, panel=True))
plate("entrust-sigma-ds2", "Entrust Sigma DS2 card issuance printer schematic", lambda d: printer_slot(d))
plate("entrust-sigma-ds3", "Entrust Sigma DS3 colour card issuance printer schematic", lambda d: printer_slot(d, colour=True))
plate("evolis-ymcko-ribbons", "YMCKO printer ribbon cartridge schematic", ribbon)
plate("evolis-cleaning-kits", "Card printer cleaning kit schematic", cleaning_kit)
plate("blank-pvc-cards", "Blank PVC card stock schematic", card_stack)
plate("evolis-accessories", "Card printer accessories schematic", accessories)
plate("idemia-sigma-family", "IDEMIA SIGMA fingerprint terminal schematic", lambda d: wall_terminal(d, reader=True))
plate("hikvision-minmoe", "Hikvision MinMoe facial recognition terminal schematic", lambda d: wall_terminal(d))
plate("idemia-visionpass", "IDEMIA VisionPass reader schematic", lambda d: wall_terminal(d, cams=2))
plate("zkteco-megaface", "ZKTeco MegaFace facial verification terminal schematic", lambda d: wall_terminal(d, cams=2, wide=True))
plate("zkteco-f18", "ZKTeco F18 fingerprint access control terminal schematic", lambda d: wall_terminal(d, keypad=True))
plate("hikvision-card-readers", "Hikvision card reader schematic", reader_wedge)
plate("morphomanager", "MorphoManager enrolment and administration console schematic", console)
plate("zkteco-handheld-metal-detectors", "Handheld metal detector wand schematic", handheld_wand)
plate("walkthrough-detectors", "Walkthrough metal detector arch schematic", walkthrough)
plate("zkteco-zk-d1090", "ZKTeco ZK-D1090 nine-zone walk-through metal detector schematic",
      lambda d: walkthrough(d, zones=9, panel=True))
plate("hikvision-colorvu", "Hikvision ColorVu bullet camera schematic", lambda d: bullet(d, warm=True))
plate("hikvision-turbo-hd", "Hikvision Turbo HD bullet camera schematic", lambda d: bullet(d, ir=True))
plate("hikvision-darkfighter", "Hikvision DarkFighter turret camera schematic", turret)
plate("hikvision-nvr", "Hikvision network video recorder schematic", nvr)


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, (title, draw) in PLATES.items():
        d = D()
        draw(d)
        with open(os.path.join(OUT, slug + ".svg"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(d.render(title))
    print(f"wrote {len(PLATES)} plates to {OUT}")


if __name__ == "__main__":
    main()
