"""Redraw the bundled section artwork in static/img/solutions/ and static/img/site/.

Run `python tools/generate_solution_posters.py` after adding a solution: a capability
with no image falls back to a text panel on its detail page, and the capability card
grid has no artwork to show.

They are illustrative graphics, not photographs of client sites: keep them that way and
never label one with a client name.

Two shapes, because two slots use them. Capability posters are 900x1200 verticals: the
solution detail page shows `image_src` as the right-hand backdrop of "What we deliver"
(a tall panel that object-fit crops), and the card grid shows it through a 16:9 window,
so every composition keeps its subject across the middle band. Site graphics are
1200x900 landscape for the dark right column of an inner-page hero.
"""

import math
import os

INK = "#0d1b20"
GROUND_TOP = "#0b161b"
GROUND_BOTTOM = "#12252c"
STEEL = "#8fb1bd"
HAIR = "#40606d"
BODY = "url(#m)"
GLASS = "url(#l)"
DEEP = "url(#d)"
BLUE = "#2a6ff0"
GREEN = "#6fd44a"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLUTIONS = os.path.join(ROOT, "static", "img", "solutions")
SITE = os.path.join(ROOT, "static", "img", "site")

LANDSCAPE = (1200, 900)
PORTRAIT = (900, 1200)


class P:
    def __init__(self, width=LANDSCAPE[0], height=LANDSCAPE[1]):
        self.w, self.h = width, height
        self.parts = []

    def el(self, tag, attrs, text=None):
        bits = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)
        self.parts.append(f"<{tag} {bits}/>" if text is None else f"<{tag} {bits}>{text}</{tag}>")

    def rect(self, x, y, w, h, r=0, fill=BODY, stroke=STEEL, sw=2, opacity=None, dash=None):
        self.el("rect", {
            "x": x, "y": y, "width": w, "height": h, "rx": r or None, "fill": fill,
            "stroke": stroke, "stroke-width": sw or None, "opacity": opacity,
            "stroke-dasharray": dash,
        })

    def circle(self, cx, cy, r, fill=None, stroke=STEEL, sw=2, opacity=None, dash=None):
        self.el("circle", {
            "cx": cx, "cy": cy, "r": r, "fill": fill, "stroke": stroke,
            "stroke-width": sw or None, "opacity": opacity, "stroke-dasharray": dash,
        })

    def ellipse(self, cx, cy, rx, ry, fill=None, stroke=STEEL, sw=2, opacity=None):
        self.el("ellipse", {
            "cx": cx, "cy": cy, "rx": rx, "ry": ry, "fill": fill, "stroke": stroke,
            "stroke-width": sw or None, "opacity": opacity,
        })

    def line(self, x1, y1, x2, y2, stroke=STEEL, sw=2, opacity=None, dash=None):
        self.el("line", {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": stroke,
            "stroke-width": sw or None, "opacity": opacity, "stroke-dasharray": dash,
        })

    def path(self, d, stroke=STEEL, sw=2, fill="none", opacity=None, dash=None):
        self.el("path", {
            "d": d, "stroke": stroke, "stroke-width": sw or None, "fill": fill,
            "opacity": opacity, "stroke-dasharray": dash,
        })

    def text(self, x, y, content, size=24, fill=STEEL, family="mono", spacing=6,
             anchor="start", opacity=None, weight=600):
        stack = ("ui-monospace, 'JetBrains Mono', 'Segoe UI', monospace" if family == "mono"
                 else "Inter, 'Segoe UI', system-ui, Arial, sans-serif")
        self.el("text", {
            "x": x, "y": y, "font-family": stack, "font-size": size, "fill": fill,
            "letter-spacing": spacing, "text-anchor": anchor, "opacity": opacity,
            "font-weight": weight,
        }, text=content)

    def bloom(self, inner):
        self.parts.append('<g filter="url(#bloom)">')
        inner()
        self.parts.append("</g>")

    def group(self, inner, transform=None):
        self.parts.append(f'<g transform="{transform}">' if transform else "<g>")
        inner()
        self.parts.append("</g>")

    # ---------------------------------------------------------------- surface
    def surface(self, kicker, index, accent=BLUE):
        """The shared plate: ink ground, brand sweep, engineering grid, registration marks.

        The caption sits below the 16:9 card window on purpose: a card shows the
        subject, the detail page shows the whole composition including its label.
        """
        self.rect(0, 0, self.w, self.h, fill="url(#ink)", stroke=None)
        self.rect(0, 0, self.w, self.h, fill="url(#sweep)", stroke=None)
        self.rect(0, 0, self.w, self.h, fill="url(#grid)", stroke=None, opacity="0.5")
        horizon = round(self.h * 0.70)
        self.line(90, horizon, self.w - 90, horizon, HAIR, 1.5, opacity="0.7")
        rake = self.h * 0.84
        for a, b in ((0.26, 0.18), (0.46, 0.44), (0.66, 0.68), (0.86, 0.9)):
            self.line(self.w * a, horizon, self.w * b, rake, HAIR, 1.25, opacity="0.45")
        for cx, cy, dx, dy in ((70, 70, 1, 1), (self.w - 70, 70, -1, 1),
                               (70, self.h - 70, 1, -1), (self.w - 70, self.h - 70, -1, -1)):
            self.line(cx, cy, cx + 34 * dx, cy, accent, 2)
            self.line(cx, cy, cx, cy + 34 * dy, accent, 2)
        if kicker:
            self.text(100, self.h - 74, kicker.upper(), 24, STEEL, spacing=7)
            self.line(100, self.h - 56, 134 + 13 * len(kicker), self.h - 56, accent, 2)
        if index:
            self.text(self.w - 100, 210, index, 118, STEEL, family="sans", spacing=0,
                      anchor="end", opacity="0.12", weight=700)

    def shadow(self, cx, cy=None, rx=300, ry=24):
        self.ellipse(cx, cy if cy is not None else round(self.h * 0.70), rx, ry,
                     fill=INK, stroke=None, opacity="0.55")

    def render(self, label):
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-label="{label}">\n'
            f"  <title>{label}</title>\n" + DEFS +
            '  <g fill="none" stroke-linecap="round" stroke-linejoin="round">\n'
            + "\n".join("    " + p for p in self.parts)
            + "\n  </g>\n</svg>\n"
        )


GRADIENTS = (
    ("ink", "linear", {"x1": 0, "y1": 0, "x2": 0.35, "y2": 1},
     ((0, GROUND_TOP), (0.55, "#0e1f26"), (1, GROUND_BOTTOM))),
    ("sweep", "radial", {"cx": 0.8, "cy": 0.12, "r": 0.95},
     ((0, "#1a4a5e"), (0.45, "#123341"), (1, "#000000"))),
    ("m", "linear", {"x1": 0, "y1": 0, "x2": 0.2, "y2": 1},
     ((0, "#31525e"), (0.55, "#1d3640"), (1, "#142630"))),
    ("l", "linear", {"x1": 0, "y1": 0, "x2": 0.4, "y2": 1},
     ((0, "#1b4150"), (0.5, "#102b35"), (1, "#0a1b22"))),
    ("d", "linear", {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
     ((0, "#16262d"), (1, "#0a1418"))),
)

PATTERNS = (("grid", 48, 48, '<path d="M48,0 L0,0 0,48" stroke="#1d3a45" stroke-width="1" fill="none"/>'),)

DEFS = "  <defs>\n" + "".join(
    '    <{0}Gradient id="{1}" {2}>{3}</{0}Gradient>\n'.format(
        kind, gid,
        " ".join(f'{k}="{v}"' for k, v in attrs.items()),
        "".join('<stop offset="{0}" stop-color="{1}"{2}/>'.format(
            o, c, ' stop-opacity="0"' if c == "#000000" else "") for o, c in stops),
    )
    for gid, kind, attrs, stops in GRADIENTS
) + "".join(
    '    <pattern id="{0}" width="{1}" height="{2}" patternUnits="userSpaceOnUse">{3}</pattern>\n'.format(*p)
    for p in PATTERNS
) + (
    '    <filter id="bloom" x="-30%" y="-30%" width="160%" height="160%">'
    '<feGaussianBlur stdDeviation="7" result="b"/><feMerge>'
    '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>\n'
    "  </defs>\n"
)


# --------------------------------------------------------------------------- helpers


def sight_cone(p, x, y, angle_deg, length, spread, colour=BLUE, opacity="0.24"):
    """A camera's field of view as a filled wedge."""
    a, b = math.radians(angle_deg - spread), math.radians(angle_deg + spread)
    p.path("M%.0f,%.0f L%.0f,%.0f A%.0f,%.0f 0 0,1 %.0f,%.0f Z"
           % (x, y, x + length * math.cos(a), y + length * math.sin(a),
              length, length, x + length * math.cos(b), y + length * math.sin(b)),
           stroke=colour, sw=1.5, fill=colour, opacity=opacity)


def camera_body(p, x, y, angle=0, scale=1):
    """A bullet camera on a bracket, drawn at the origin then placed and rotated."""
    p.group(lambda: (
        p.path("M0,26 L0,54 L34,54", stroke=STEEL, sw=6),
        p.rect(-6, 48, 46, 12, 4, fill=BODY, stroke=STEEL, sw=3),
        p.group(lambda: (
            p.rect(-96, -26, 128, 52, 16, fill=BODY, stroke=STEEL, sw=4),
            p.path("M32,-26 L58,-16 L58,16 L32,26", fill=GLASS, stroke=STEEL, sw=4),
            p.circle(64, 0, 13, fill=DEEP, stroke=STEEL, sw=3),
            p.circle(64, 0, 5, fill=BLUE, stroke=None),
            p.rect(-84, -34, 44, 10, 5, fill=DEEP, stroke=STEEL, sw=3),
            p.line(-60, 14, 10, 14, HAIR, 3),
        ), "rotate(%.0f)" % angle),
    ), "translate(%d %d) scale(%.2f)" % (x, y, scale))


def cabinet(p, x, y, w, h, led=6, glow=True):
    """A network cabinet with a perforated door and a status column."""
    p.rect(x, y, w, h, 8, fill=BODY, stroke=STEEL, sw=3)
    p.rect(x + 10, y + 10, w - 20, h - 20, 5, fill=DEEP, stroke=HAIR, sw=2)
    for i in range(led):
        row = y + 26 + i * ((h - 56) / max(led - 1, 1))
        p.line(x + 22, row, x + w - 34, row, HAIR, 3)
        p.circle(x + w - 24, row, 3.5, fill=GREEN if i % 3 else BLUE, stroke=None)
    if glow:
        p.bloom(lambda: p.rect(x + 18, y + h - 26, w - 36, 6, 3, fill=BLUE, stroke=None))


def card_glyph(p, x, y, w=170, h=106, angle=0):
    p.group(lambda: (
        p.rect(0, 0, w, h, 12, fill=BODY, stroke=STEEL, sw=3),
        p.rect(16, 20, 36, 27, 5, fill=None, stroke=BLUE, sw=3),
        p.line(24, 31, 44, 31, BLUE, 2),
        p.line(64, 24, w - 18, 24, HAIR, 3),
        p.line(64, 37, w - 40, 37, HAIR, 2.5),
        p.line(16, h - 28, w - 16, h - 28, GREEN, 5),
        p.rect(16, h - 19, 52, 7, 3, fill=HAIR, stroke=None),
    ), "translate(%d %d) rotate(%.0f)" % (x, y, angle))


def door_leaf(p, x, y, w, h):
    """A glass leaf with a mullion, a push bar and a handle."""
    p.rect(x, y, w, h, 4, fill=GLASS, stroke=STEEL, sw=5)
    p.line(x + w / 2, y + 8, x + w / 2, y + h - 8, HAIR, 3)
    p.line(x + 14, y + h * 0.42, x + w - 14, y + h * 0.42, HAIR, 2.5)
    p.rect(x + w - 26, y + h * 0.5, 10, 84, 5, fill=BODY, stroke=STEEL, sw=3)
    p.line(x + 10, y + h - 24, x + w - 10, y + h - 24, HAIR, 3)


def reader(p, x, y, colour=GREEN):
    p.rect(x, y, 52, 82, 8, fill=BODY, stroke=STEEL, sw=3)
    p.rect(x + 9, y + 11, 34, 29, 4, fill=DEEP, stroke=HAIR, sw=2)
    p.circle(x + 26, y + 56, 6, fill=colour, stroke=None)
    p.bloom(lambda: p.circle(x + 26, y + 56, 4, fill=colour, stroke=None))


def building_block(p, x, y, w, h, cols=4, rows=6):
    p.rect(x, y, w, h, 6, fill=BODY, stroke=STEEL, sw=3)
    for r in range(rows):
        for c in range(cols):
            wx = x + 18 + c * ((w - 40) / cols)
            wy = y + 18 + r * ((h - 36) / rows)
            p.rect(wx, wy, (w - 40) / cols - 10, (h - 36) / rows - 12, 2,
                   fill=DEEP, stroke=HAIR, sw=1.5)


def findings_strip(p, x, y, w, rows=4, cols=3, label="RISK REGISTER"):
    """A ruled register block: the bottom-band detail a card window crops away."""
    p.line(x, y - 26, x + w, y - 26, HAIR, 1.5, opacity="0.7")
    p.text(x, y - 34, label, 20, STEEL, spacing=5, opacity="0.85")
    colw = w / cols
    for i in range(rows * cols):
        c, r = i % cols, i // cols
        bx, by = x + c * colw, y + r * 42
        p.line(bx + 26, by + 10, bx + colw - 16, by + 10, HAIR, 2.5, opacity="0.6")
        p.rect(bx, by, 16, 16, 3, fill=None, stroke=HAIR, sw=2)
        if (c * 7 + r * 3) % 4 == 0:
            p.path("M%d,%d l6,6 12,-13" % (bx + 2, by + 4), stroke=GREEN, sw=3.5)


# --------------------------------------------------------------------------- capability posters


def access_control(p):
    p.surface("Access control", "02", BLUE)
    p.shadow(450, rx=286)
    p.rect(250, 300, 400, 540, 6, fill=DEEP, stroke=STEEL, sw=7)
    p.line(250, 322, 650, 322, HAIR, 3)
    door_leaf(p, 272, 340, 356, 480)
    p.bloom(lambda: (
        p.circle(450, 578, 202, stroke=GREEN, sw=2.5, opacity="0.5", dash="3 14"),
        p.circle(450, 578, 252, stroke=GREEN, sw=1.5, opacity="0.24", dash="2 20"),
    ))
    reader(p, 146, 516)
    p.bloom(lambda: p.path("M198,574 C240,580 250,596 272,620", stroke=BLUE, sw=3, dash="4 12"))
    card_glyph(p, 296, 636, angle=-8)
    # the controller stands off to the right, wired down to the floor and back to the jamb
    p.rect(662, 660, 152, 108, 8, fill=BODY, stroke=STEEL, sw=3)
    p.line(678, 690, 798, 690, HAIR, 3)
    p.line(678, 714, 764, 714, HAIR, 2.5)
    p.rect(678, 738, 42, 10, 4, fill=GREEN, stroke=None)
    p.rect(728, 738, 42, 10, 4, fill=BLUE, stroke=None)
    for ny in (690, 714, 738):
        p.line(650, ny - 6, 662, ny - 6, HAIR, 2, dash="4 8")
    p.line(738, 768, 738, 840, HAIR, 2.5, dash="6 9")
    p.text(100, 990, "CREDENTIAL", 19, STEEL, spacing=5, opacity="0.7")
    p.line(100, 1006, 250, 1006, HAIR, 2, opacity="0.7")
    for i, tag in enumerate(("PREMISES", "TIME & ATTENDANCE", "VISITOR")):
        tx = 100 + i * 250
        p.rect(tx, 1032, 12, 12, 3, fill=None, stroke=HAIR, sw=2)
        p.path("M%d,%d l4,5 9,-10" % (tx + 1, 1035), stroke=GREEN, sw=3)
        p.text(tx + 24, 1043, tag, 19, STEEL, spacing=4, opacity="0.8")


def data_centre(p):
    p.surface("Data centre build", "04", BLUE)
    p.shadow(450, rx=330)
    # overhead containment tray with rungs, and the drops that come off it
    p.rect(100, 244, 700, 42, 6, fill=BODY, stroke=STEEL, sw=3)
    for tx in range(124, 790, 42):
        p.line(tx, 248, tx, 282, HAIR, 2.5)
    p.bloom(lambda: p.line(112, 300, 788, 300, BLUE, 2, opacity="0.5"))
    cabinet(p, 62, 340, 214, 500, led=8)
    cabinet(p, 624, 340, 214, 500, led=8)
    # the far row reads as the end of the aisle, so it is smaller and dimmer
    p.group(lambda: (
        cabinet(p, 300, 400, 92, 300, led=4, glow=False),
        cabinet(p, 404, 400, 92, 300, led=4, glow=False),
    ), "opacity(0.8)")
    p.bloom(lambda: (
        p.rect(288, 380, 12, 340, 6, fill=BLUE, stroke=None, opacity="0.5"),
        p.rect(600, 380, 12, 340, 6, fill=BLUE, stroke=None, opacity="0.5"),
    ))
    # raised floor: perforated tiles in perspective toward the aisle
    for ty in (880, 924, 972, 1024):
        p.line(60, ty, 840, ty, HAIR, 1.5, opacity="0.55")
    for tx in range(60, 841, 78):
        p.line(tx, 860, tx + (tx - 450) * 0.34, 1024, HAIR, 1.25, opacity="0.4")
    p.text(100, 1096, " conditioned air  ·  bonded earth  ·  documented paths", 21, STEEL,
           spacing=2, opacity="0.75", family="sans", weight=400)


def risk_consultancy(p):
    p.surface("Risk consultancy", "05", GREEN)
    # plan view: a fenced site boundary, three defence rings and the assessed zones
    p.rect(100, 250, 700, 640, 14, fill=DEEP, stroke=STEEL, sw=3, dash="22 12")
    for fx in range(124, 801, 60):
        p.line(fx, 250, fx - 16, 224, HAIR, 2, opacity="0.8")
    p.circle(450, 570, 296, stroke=GREEN, sw=2, opacity="0.32", dash="4 16")
    p.circle(450, 570, 212, stroke=GREEN, sw=2.5, opacity="0.48", dash="4 14")
    p.circle(450, 570, 128, stroke=GREEN, sw=3, opacity="0.66", dash="4 12")
    p.bloom(lambda: p.circle(450, 570, 58, stroke=GREEN, sw=3, opacity="0.9"))
    for zx, zy, zw, zh in ((150, 296, 140, 92), (612, 288, 144, 100),
                           (146, 706, 150, 100), (606, 712, 152, 106)):
        p.rect(zx, zy, zw, zh, 6, fill=BODY, stroke=STEEL, sw=2.5)
        p.line(zx + 12, zy + 26, zx + zw - 12, zy + 26, HAIR, 2.5)
        p.line(zx + 12, zy + 46, zx + zw - 44, zy + 46, HAIR, 2)
    p.path("M450,522 C450,522 486,566 450,610 C414,566 450,522 450,522 Z", fill=BODY, stroke=GREEN, sw=4)
    p.circle(450, 548, 14, fill=DEEP, stroke=GREEN, sw=4)
    p.circle(450, 548, 5, fill=GREEN, stroke=None)
    findings_strip(p, 100, 960, 700)


def assessments(p):
    p.surface("Site assessment", "06", BLUE)
    p.shadow(320, rx=250)
    building_block(p, 110, 320, 400, 520)
    p.line(80, 840, 560, 840, STEEL, 4)
    # a pole camera at the right covers the elevation, its cones bloomed over the facade
    p.path("M700,320 L700,840", stroke=STEEL, sw=7)
    p.rect(652, 300, 96, 22, 6, fill=BODY, stroke=STEEL, sw=3)
    camera_body(p, 680, 376, angle=178, scale=0.8)
    p.bloom(lambda: (
        sight_cone(p, 596, 370, 176, 460, 20),
        sight_cone(p, 596, 370, 206, 400, 14, BLUE, "0.16"),
    ))
    camera_body(p, 150, 716, angle=6, scale=0.62)
    p.bloom(lambda: sight_cone(p, 250, 722, 350, 360, 15, GREEN, "0.16"))
    # the survey lens: the same facade, looked at closely
    p.circle(300, 486, 76, stroke=BLUE, sw=5, opacity="0.95")
    p.line(356, 542, 402, 588, BLUE, 8)
    p.circle(300, 486, 76, fill=BLUE, stroke=None, opacity="0.1")
    findings_strip(p, 100, 928, 700, rows=3, cols=3, label="SURVEY RECORD")


# --------------------------------------------------------------------------- site graphics


def one_system(p):
    p.surface("One accountable team", "", BLUE)
    cx, cy = 600, 452
    p.circle(cx, cy, 268, stroke=HAIR, sw=2, opacity="0.5", dash="3 15")
    p.bloom(lambda: p.circle(cx, cy, 268, stroke=BLUE, sw=1.5, opacity="0.3", dash="3 40"))
    for i, draw in enumerate((camera, door, fence, cabinet_small, document, chart)):
        rad = math.radians(-90 + i * 60)
        nx, ny = cx + 268 * math.cos(rad), cy + 268 * math.sin(rad)
        p.line(cx + 92 * math.cos(rad), cy + 92 * math.sin(rad),
               nx - 52 * math.cos(rad), ny - 52 * math.sin(rad), HAIR, 2, opacity="0.75", dash="5 9")
        p.circle(nx, ny, 66, fill=DEEP, stroke=STEEL, sw=3)
        draw(p, nx, ny)
    p.circle(cx, cy, 96, fill=BODY, stroke=STEEL, sw=4)
    p.bloom(lambda: p.circle(cx, cy, 96, stroke=GREEN, sw=2, opacity="0.55"))
    p.circle(cx, cy, 58, fill=DEEP, stroke=HAIR, sw=2)
    p.path("M%d,%d l26,26 52,-58" % (cx - 40, cy + 6), stroke=GREEN, sw=7)
    p.line(cx - 46, cy - 40, cx + 46, cy - 40, HAIR, 3)
    for ry in (-24, 40):
        p.line(cx - 58, cy + ry, cx + 58, cy + ry, HAIR, 2, opacity="0.6")


def camera(p, cx, cy):
    p.rect(cx - 34, cy - 14, 56, 24, 10, fill=BODY, stroke=STEEL, sw=2.5)
    p.path("M%d,%d L%d,%d %d,%d %d,%d Z" % (cx + 22, cy - 14, cx + 40, cy - 7, cx + 40, cy + 7, cx + 22, cy + 14),
           fill=GLASS, stroke=STEEL, sw=2.5)
    p.circle(cx + 34, cy, 5, fill=BLUE, stroke=None)
    p.path("M%d,%d L%d,%d %d,%d" % (cx - 20, cy + 10, cx - 20, cy + 24, cx + 4, cy + 24), stroke=STEEL, sw=3)


def door(p, cx, cy):
    p.rect(cx - 26, cy - 34, 52, 68, 4, fill=DEEP, stroke=STEEL, sw=2.5)
    p.circle(cx + 14, cy, 4, fill=GREEN, stroke=None)
    p.line(cx - 26, cy - 34, cx - 44, cy - 44, STEEL, 2.5)
    p.rect(cx - 48, cy - 6, 18, 12, 3, fill=BODY, stroke=STEEL, sw=2)


def fence(p, cx, cy):
    for i in range(4):
        px = cx - 36 + i * 24
        p.line(px, cy - 24, px, cy + 24, STEEL, 3)
    p.line(cx - 40, cy - 10, cx + 40, cy - 10, STEEL, 2.5)
    p.line(cx - 40, cy + 12, cx + 40, cy + 12, STEEL, 2.5)
    for i in range(5):
        p.path("M%d,%d l10,-14" % (cx - 44 + i * 22, cy - 24), stroke=GREEN, sw=2.5)


def cabinet_small(p, cx, cy):
    p.rect(cx - 26, cy - 34, 52, 68, 5, fill=BODY, stroke=STEEL, sw=2.5)
    for i in range(4):
        p.line(cx - 16, cy - 22 + i * 15, cx + 12, cy - 22 + i * 15, HAIR, 2.5)
        p.circle(cx + 20, cy - 22 + i * 15, 2.5, fill=GREEN if i % 2 else BLUE, stroke=None)


def document(p, cx, cy):
    p.path("M%d,%d h40 l14,14 v46 h-54 Z" % (cx - 27, cy - 32), fill=DEEP, stroke=STEEL, sw=2.5)
    p.path("M%d,%d h40 l14,14" % (cx - 27, cy - 32), stroke=STEEL, sw=2.5)
    for i in range(3):
        p.line(cx - 15, cy - 8 + i * 15, cx + 17, cy - 8 + i * 15, HAIR, 2.5)


def chart(p, cx, cy):
    p.line(cx - 34, cy + 26, cx + 34, cy + 26, STEEL, 2.5)
    p.line(cx - 34, cy + 26, cx - 34, cy - 30, STEEL, 2.5)
    for i, bh in enumerate((20, 34, 26, 44)):
        p.rect(cx - 24 + i * 16, cy + 26 - bh, 11, bh, 2, fill=BODY, stroke=HAIR, sw=2)
    p.path("M%d,%d l16,-14 16,8 16,-24" % (cx - 24, cy + 4), stroke=GREEN, sw=3)


def coverage(p):
    p.surface("Nairobi", "", BLUE)
    # an abstract road grid, not a surveyed street map: rings and a pin, nothing measured
    for gx in range(140, 1061, 92):
        p.line(gx, 168, gx + (gx - 600) * 0.1, 712, HAIR, 1.75, opacity="0.5")
    for gy in range(168, 713, 72):
        p.line(150, gy, 1050, gy, HAIR, 1.75, opacity="0.45")
    p.path("M150,540 C420,470 640,600 1050,470", stroke=STEEL, sw=4, opacity="0.65")
    p.path("M300,168 C360,420 520,520 700,712", stroke=STEEL, sw=3, opacity="0.4")
    for bx, by, bw, bh in ((240, 240, 120, 74), (820, 214, 150, 92), (206, 588, 140, 82),
                           (846, 596, 128, 74), (636, 226, 96, 62)):
        p.rect(bx, by, bw, bh, 5, fill=DEEP, stroke=HAIR, sw=2)
    cx, cy = 600, 452
    # the ground is dimmed under the marker so the callout stays readable
    p.circle(cx, cy, 214, fill=INK, stroke=None, opacity="0.62")
    for r, tone in ((150, GREEN), (258, BLUE), (366, HAIR)):
        p.circle(cx, cy, r, stroke=tone, sw=2.5 if r < 300 else 2,
                 opacity="0.55" if r < 300 else "0.4", dash="4 14")
    p.bloom(lambda: p.circle(cx, cy, 150, stroke=GREEN, sw=1.5, opacity="0.4", dash="4 40"))
    p.path("M%d,%d C%d,%d %d,%d %d,%d C%d,%d %d,%d %d,%d Z"
           % (cx, cy + 34, cx - 40, cy - 14, cx - 30, cy - 62, cx, cy - 62,
              cx + 30, cy - 62, cx + 40, cy - 14, cx, cy + 34),
           fill=BODY, stroke=BLUE, sw=4)
    p.circle(cx, cy - 26, 15, fill=DEEP, stroke=BLUE, sw=4)
    p.circle(cx, cy - 26, 5, fill=GREEN, stroke=None)
    p.line(cx + 44, cy - 30, cx + 96, cy - 58, STEEL, 2, opacity="0.8")
    p.rect(cx + 100, cy - 104, 264, 62, 8, fill=DEEP, stroke=STEEL, sw=2)
    p.text(cx + 118, cy - 80, "MOI AVENUE", 21, STEEL, spacing=5)
    p.text(cx + 118, cy - 56, "NAIROBI, KENYA", 19, STEEL, spacing=5, opacity="0.7")


def route_not_found(p):
    p.w, p.h = 600, 400
    p.rect(0, 0, 600, 400, fill="url(#ink)", stroke=None)
    p.rect(0, 0, 600, 400, fill="url(#sweep)", stroke=None)
    p.rect(0, 0, 600, 400, fill="url(#grid)", stroke=None, opacity="0.45")
    p.line(24, 52, 58, 52, BLUE, 2)
    p.line(24, 52, 24, 86, BLUE, 2)
    p.line(576, 348, 542, 348, BLUE, 2)
    p.line(576, 348, 576, 314, BLUE, 2)
    p.circle(96, 176, 16, fill=DEEP, stroke=STEEL, sw=3)
    p.circle(96, 176, 5, fill=GREEN, stroke=None)
    p.path("M112,176 C200,176 210,104 300,104 C372,104 380,160 428,160", stroke=STEEL, sw=3.5, dash="10 14")
    p.rect(428, 134, 84, 52, 8, fill=DEEP, stroke=HAIR, sw=3, dash="8 10")
    p.line(450, 160, 490, 160, HAIR, 3)
    p.bloom(lambda: p.circle(300, 104, 30, stroke=BLUE, sw=2, opacity="0.6", dash="3 12"))
    p.text(74, 300, "404", 88, STEEL, family="sans", spacing=0, weight=700)
    p.text(212, 282, "OFF THE ROUTE", 22, STEEL, spacing=6)
    p.line(212, 296, 388, 296, BLUE, 2)


PLATES = (
    (SOLUTIONS, "access-control", "Access control", access_control, PORTRAIT),
    (SOLUTIONS, "data-centre-construction", "Data centre construction", data_centre, PORTRAIT),
    (SOLUTIONS, "security-risk-consultancy", "Security risk consultancy", risk_consultancy, PORTRAIT),
    (SOLUTIONS, "security-assessments", "Security assessments", assessments, PORTRAIT),
    (SITE, "one-system", "One accountable team", one_system, LANDSCAPE),
    (SITE, "coverage-nairobi", "Coverage from Nairobi", coverage, LANDSCAPE),
    (SITE, "not-found", "Page not found", route_not_found, LANDSCAPE),
)


def main():
    for folder, slug, label, draw, size in PLATES:
        os.makedirs(folder, exist_ok=True)
        doc = P(*size)
        draw(doc)
        target = os.path.join(folder, f"{slug}.svg")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(doc.render(label))
        print(f"  wrote {os.path.relpath(target, ROOT)}")
    print(f"wrote {len(PLATES)} posters")


if __name__ == "__main__":
    main()
