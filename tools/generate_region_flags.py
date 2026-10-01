"""Draw the country marks for the home page's "beyond Kenya" band.

The band shipped with emoji flags, which are not rendered as flags on Windows or in
most Linux/server font stacks - they come out as two regional-indicator letters
("KE", "UG"). These are our own redraws: real flag geometry, cropped to a 96px
circle so it can sit in the round card without a CSS mask.

Output: static/img/flags/<iso>.svg. Run `python tools/generate_region_flags.py`, then
`collectstatic` for a deployment. The template lists the codes, and
`core.tests.HomeTests.test_every_region_card_ships_a_flag` fails if the two drift.
"""

from __future__ import annotations

import math
from pathlib import Path

SIZE = 96
CENTER = SIZE / 2
FLAGS_DIR = Path(__file__).resolve().parent.parent / "static" / "img" / "flags"

WHITE = "#ffffff"
BLACK = "#111111"
GREEN = "#006600"
GREEN_BRIGHT = "#1EB53A"
GREEN_ETHIO = "#078930"
GREEN_SUDAN = "#007229"
RED = "#BB0000"
RED_BRIGHT = "#D21034"
RED_ETHIO = "#DA121A"
YELLOW = "#FCDC00"
YELLOW_SOFT = "#FCD116"
BLUE_SKY = "#418FDE"
BLUE_RWANDA = "#00A1F1"
BLUE_TANZANIA = "#00A3DD"
BLUE_ETHIO = "#0F47AF"
GREY_CRANE = "#8a8f8d"


def rect(x, y, width, height, fill):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}"/>'


def polygon(points, fill, stroke=None, stroke_width=0):
    body = " ".join(f"{x},{y}" for x, y in points)
    edge = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return f'<polygon points="{body}" fill="{fill}"{edge}/>'


def circle(cx, cy, radius, fill, stroke=None, stroke_width=0):
    edge = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}"{edge}/>'


def line(points, stroke, stroke_width):
    (x1, y1), (x2, y2) = points
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}"'
        f' stroke-width="{stroke_width}" stroke-linecap="round"/>'
    )


def star_path(cx, cy, outer, inner, points=5, rotation=-90.0):
    """A filled n-pointed star: outer tips and inner notches alternate around the ring."""
    vertices = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = math.radians(rotation + i * 180.0 / points)
        vertices.append(f"{cx + radius * math.cos(angle):.2f},{cy + radius * math.sin(angle):.2f}")
    return "M" + " L".join(vertices) + "Z"


def ray_band(cx, cy, inner_radius, length, count, width_degrees, fill, start=0.0):
    """Rays around a disc, each a narrow triangle - used by the Rwandan sun."""
    rays = []
    half = math.radians(width_degrees / 2)
    for i in range(count):
        angle = math.radians(start + i * 360.0 / count)
        base_a, base_b = angle - half, angle + half
        tips = (
            (cx + inner_radius * math.cos(base_a), cy + inner_radius * math.sin(base_a)),
            (cx + inner_radius * math.cos(base_b), cy + inner_radius * math.sin(base_b)),
            (cx + (inner_radius + length) * math.cos(angle), cy + (inner_radius + length) * math.sin(angle)),
        )
        rays.append(polygon(tips, fill))
    return "".join(rays)


def shield():
    """A Maasai-style shield with crossed spears, centred on the flag. The spears are
    drawn first and run well past the shield, because on the real flag the points and
    the ferrules are what make the emblem readable at small sizes."""
    clip = (
        '<clipPath id="kenya-shield"><ellipse cx="48" cy="48" rx="13" ry="27"/></clipPath>'
    )
    body = (
        '<g clip-path="url(#kenya-shield)">'
        + rect(35, 21, 26, 14, BLACK)
        + rect(35, 35, 26, 26, RED)
        + rect(35, 61, 26, 14, BLACK)
        + rect(46.5, 21, 3, 54, WHITE)
        + rect(39, 44, 18, 2.4, WHITE)
        + rect(39, 50, 18, 2.4, WHITE)
        + "</g>"
        + '<ellipse cx="48" cy="48" rx="13" ry="27" fill="none" stroke="{}" stroke-width="1.6"/>'.format(BLACK)
    )
    spears = (
        line(((24, 15), (72, 81)), WHITE, 2.8)
        + line(((72, 15), (24, 81)), WHITE, 2.8)
        + polygon(((24, 15), (29, 18), (24.5, 23)), WHITE)
        + polygon(((72, 15), (67, 18), (71.5, 23)), WHITE)
        + polygon(((24, 81), (29, 78), (24.5, 73)), WHITE)
        + polygon(((72, 81), (67, 78), (71.5, 73)), WHITE)
    )
    return clip + spears + body


def crane():
    """The grey crowned crane, reduced to the shapes that still read at 96px."""
    return (
        circle(48, 48, 23, WHITE)
        + '<path d="M33 57c3-8 11-11 18-10l7 1c-1 7-6 12-13 13-6 1-11 0-12-4z" fill="{}"/>'.format(GREY_CRANE)
        + '<path d="M38 60c5 2 10 2 15-1" fill="none" stroke="{}" stroke-width="1.4"/>'.format(BLACK)
        + '<path d="M56 49c1-8-1-13-5-16" fill="none" stroke="{}" stroke-width="4" stroke-linecap="round"/>'.format(GREY_CRANE)
        + circle(51, 32, 4.6, GREY_CRANE)
        + polygon(((54.5, 31), (61, 32.5), (54.5, 34.5)), YELLOW)
        + '<path d="M47 28c-1-3 0-5 2-6M50.5 27c0-3 2-5 4-5M54 28c2-2 4-2 6-1" fill="none" stroke="{}" stroke-width="2" stroke-linecap="round"/>'.format(YELLOW)
        + '<ellipse cx="52.5" cy="38" rx="2.2" ry="3.2" fill="{}"/>'.format(RED_BRIGHT)
        + line(((42, 64), (40, 70)), "#6f7472", 1.6)
        + line(((49, 65), (49, 70)), "#6f7472", 1.6)
    )


def kenya():
    return (
        rect(0, 0, SIZE, 30, BLACK)
        + rect(0, 30, SIZE, 3, WHITE)
        + rect(0, 33, SIZE, 30, RED)
        + rect(0, 63, SIZE, 3, WHITE)
        + rect(0, 66, SIZE, 30, GREEN)
        + shield()
    )


def uganda():
    bands = [(0, BLACK), (16, YELLOW), (32, RED), (48, BLACK), (64, YELLOW), (80, RED)]
    return "".join(rect(0, y, SIZE, 16, fill) for y, fill in bands) + crane()


def tanzania():
    return (
        polygon(((0, 0), (SIZE, 0), (0, SIZE)), GREEN_BRIGHT)
        + polygon(((SIZE, SIZE), (SIZE, 0), (0, SIZE)), BLUE_TANZANIA)
        + line(((SIZE + 6, -6), (-6, SIZE + 6)), YELLOW_SOFT, 30)
        + line(((SIZE + 6, -6), (-6, SIZE + 6)), BLACK, 21)
    )


def somalia():
    return rect(0, 0, SIZE, SIZE, BLUE_SKY) + '<path d="{}" fill="{}"/>'.format(
        star_path(CENTER, CENTER, 22, 9), WHITE
    )


def sudan():
    return (
        rect(0, 0, SIZE, 32, RED_BRIGHT)
        + rect(0, 32, SIZE, 32, WHITE)
        + rect(0, 64, SIZE, 32, BLACK)
        + polygon(((0, 0), (36, CENTER), (0, SIZE)), GREEN_SUDAN)
    )


def rwanda():
    return (
        rect(0, 0, SIZE, 48, BLUE_RWANDA)
        + rect(0, 48, SIZE, 24, YELLOW)
        + rect(0, 72, SIZE, 24, GREEN_BRIGHT)
        + ray_band(66, 24, 8.5, 7, 12, 9, YELLOW_SOFT)
        + circle(66, 24, 8.5, YELLOW_SOFT)
    )


def ethiopia():
    points = []
    for i in range(5):
        angle = math.radians(-90 + i * 72)
        points.append((CENTER + 15 * math.cos(angle), CENTER + 15 * math.sin(angle)))
    pentagram = "M" + " L".join(
        f"{points[(i * 2) % 5][0]:.2f},{points[(i * 2) % 5][1]:.2f}" for i in range(6)
    ) + "Z"
    rays = "".join(
        line(
            (
                (CENTER + 17 * math.cos(math.radians(-90 + i * 72 + 36)),
                 CENTER + 17 * math.sin(math.radians(-90 + i * 72 + 36))),
                (CENTER + 21 * math.cos(math.radians(-90 + i * 72 + 36)),
                 CENTER + 21 * math.sin(math.radians(-90 + i * 72 + 36))),
            ),
            YELLOW,
            1.8,
        )
        for i in range(5)
    )
    return (
        rect(0, 0, SIZE, 32, GREEN_ETHIO)
        + rect(0, 32, SIZE, 32, YELLOW)
        + rect(0, 64, SIZE, 32, RED_ETHIO)
        + circle(CENTER, CENTER, 24, BLUE_ETHIO)
        + '<path d="{}" fill="none" stroke="{}" stroke-width="2.4" stroke-linejoin="round"/>'.format(pentagram, YELLOW)
        + rays
    )


FLAGS = {
    "ke": ("Kenya", kenya),
    "ug": ("Uganda", uganda),
    "tz": ("Tanzania", tanzania),
    "so": ("Somalia", somalia),
    "sd": ("Sudan", sudan),
    "rw": ("Rwanda", rwanda),
    "et": ("Ethiopia", ethiopia),
}


def document(name, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}"'
        f' width="{SIZE}" height="{SIZE}" role="img" aria-label="{name} flag">'
        f'<title>{name}</title>'
        f'<clipPath id="disc"><circle cx="{CENTER}" cy="{CENTER}" r="{CENTER}"/></clipPath>'
        f'<g clip-path="url(#disc)">{body}</g>'
        f'<circle cx="{CENTER}" cy="{CENTER}" r="{CENTER - 0.5}" fill="none" stroke="rgba(10,31,43,0.16)"/>'
        f"</svg>\n"
    )


def main():
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    for code, (name, draw) in FLAGS.items():
        path = FLAGS_DIR / f"{code}.svg"
        path.write_text(document(name, draw()), encoding="utf-8")
        print(f"wrote {path.relative_to(FLAGS_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
