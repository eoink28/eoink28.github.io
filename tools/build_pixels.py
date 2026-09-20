#!/usr/bin/env python3
"""Build the site's pixel art and write it into the pages.

Every drawing lives in this file as a text grid, one character per pixel. Running the
script turns each grid into compact SVG paths and replaces the matching
<!-- px:name --> ... <!-- /px:name --> blocks in the HTML.

    python3 tools/build_pixels.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = [ROOT / "index.html", ROOT / "privacy.html", ROOT / "404.html", ROOT / "writing" / "index.html", ROOT / "tools" / "og.html"]
FAVICON = ROOT / "assets" / "img" / "favicon.svg"

# The favicon is a standalone file, so it carries its own colours for the head.
FAVICON_FILLS = {
    "k": "#1a1a1f", "h1": "#e0672c", "h2": "#b04a1e", "h3": "#f59a55",
    "s1": "#f5c6a0", "s2": "#dc9f7c", "m": "#7a2a20",
}

# Character in a grid -> CSS class (colours live in site.css).
COLOURS = {
    "K": "k",   # outline
    "H": "h1", "h": "h2", "L": "h3",   # ginger hair and beard
    "S": "s1", "s": "s2",              # skin
    "M": "m",                          # mouth
    "W": "w",                          # white
    "R": "r1", "r": "r2",              # red top
    "G": "g", "Y": "y",                # belt, buckle
    "B": "b1", "b": "b2",              # trousers
    "O": "o1", "o": "o2",              # hiking boots
    "P": "p1", "p": "p2",              # brain
    "X": "x1", "x": "x2",              # heart
    "N": "n1", "n": "n2", "V": "v",    # rock, shaded rock, snow
    "T": "t1", "t": "t2",              # grass
    "F": "f",                          # flag
    "Z": "sh",                         # floor shadow
}


# ---------------------------------------------------------------- the character (32 x 75)

def body_row(arm_left, torso, arm_right):
    return ".." + arm_left + "K" + torso + "K" + arm_right + ".."


RED_TORSO = "RRRRRRRRRRRRRRRRrr"
TROUSERS = "BBBBBBBBBBBBBBBBbb"
LEGS = "BBBBBBbK..KBBBBBbb"

EOIN = [
    "............KKKKKKKK............",
    "..........KKLLHHHHLLKK..........",
    ".........KLHHHHHHHHHHLK.........",
    "........KHHHLHHHHHHLHHHK........",
    "........KHHHHHHHHHHHHHhK........",
    ".......KhHHHHHHHHHHHHHHhK.......",
    ".......KhHHhSSSSSSSShHHhK.......",
    ".......KhHhSSSSSSSSSShHhK.......",
    "......KKhhSSSSSSSSSSSShhKK......",
    "......KShSShhSSSSSShhSShSK......",
    "......KSsSSSKSSSSSSKSSSsSK......",
    "......KSsSSSKSSssSSKSSSsSK......",
    ".......KSSSSSSSssSSSSSSSK.......",
    ".......KHSSSSSSSSSSSSSSHK.......",
    ".......KHHSSSHHHHHHSSSHHK.......",
    ".......KHHHHHHMMMMHHHHHHK.......",
    ".......KhHHHHHHHHHHHHHHhK.......",
    "........KhHHHHHHHHHHHHhK........",
    ".........KhhHHHHHHHHhhK.........",
    "...........KKhhhhhhKK...........",
    ".............KssssK.............",
    ".........KKKKWSSSSWKKKK.........",
    ".......KKRRRRWWSSWWRRRRKK.......",
    ".....KKRRRRRRRWWWWRRRRRRRKK.....",
    "....KRRRRRRRRRRWWRRRRRRRRRRK....",
    "...KRRRRRRRRRRRRRRRRRRRRRRRRK...",
    "...KRRrRRRRRRRRRRRRRRRRRRrRRK...",
    "..KRRRrKRRRRRRRRRRRRRRRRKrRRRK..",
    *[body_row("KRRr", RED_TORSO, "rRRK")] * 3,
    body_row("KWWW", RED_TORSO, "WWWK"),
    *[body_row("KSSs", RED_TORSO, "sSSK")] * 10,
    body_row("KSSs", "GGGGGGGGYYGGGGGGGG", "sSSK"),
    *[body_row("KSSs", TROUSERS, "sSSK")] * 2,
    body_row("KSSS", TROUSERS, "SSSK"),
    body_row("KKKK", TROUSERS, "KKKK"),
    *[body_row("....", TROUSERS, "....")] * 5,
    body_row("....", "BBBBBBBbKKBBBBBBbb", "...."),
    *[body_row("....", LEGS, "....")] * 16,
    body_row("....", "OWOWOOoK..KOWOWOOo", "...."),
    *[body_row("....", "OOOOOOoK..KOOOOOOo", "....")] * 2,
    ".....KOOOOOOOoK..KOOOOOOOoK.....",
    ".....KGGGGGGGGK..KGGGGGGGGK.....",
    "......KKKKKKKK....KKKKKKKK......",
]

FLOOR_SHADOW = ["..." + "Z" * 26 + "..."]

BLINK = ["S......S", "S......S"]

# The eyes sit on their own so they can follow the pointer. The cover hides the pair
# drawn into the body, then these are painted on top.
EYES = ["K......K", "K......K"]

BRAIN = [
    "...KKKKKKKK...",
    "..KPPPpPPpPPK.",
    ".KPpPPPKPPPpPK",
    ".KPPPpPKPpPPPK",
    ".KpPPPpKPPPpPK",
    "..KPPpPKPpPPK.",
    "...KKKKKKKKK..",
]

SPARK = [".Y.", "YWY", ".Y."]

MOUTH_OPEN = ["KWWK", "KMMK"]

SPEECH = [
    "..KKKKKKKKKK..",
    ".KWWWWWWWWWWK.",
    "KWWWWWWWWWWWWK",
    "KWWWWWWWWWWWWK",
    "KWWWWWWWWWWWWK",
    ".KWWWWWWWWWWK.",
    "..KWKKKKKKKK..",
    ".KWK..........",
    "KK............",
]

HEART_WINDOW = [
    ".KKKKKKKKK.",
    *["KKKKKKKKKKK"] * 7,
    ".KKKKKKKKK.",
]

HEART = [
    "...........",
    "..XX...XX..",
    ".XXWX.XXXx.",
    ".XWXXXXXXx.",
    ".XXXXXXXXx.",
    "..XXXXXXx..",
    "...XXXXx...",
    "....XXx....",
    ".....x.....",
]

FLAG = [
    "KKKK",
    "KFFK",
    "KFK.",
    "KK..",
    "K...",
    "K...",
]


def mountain(height, slope, snow_rows):
    half_max = int((height - 1) * slope) + 1
    width = half_max * 2 + 1
    peak = half_max
    top = ["."] * width
    top[peak] = "K"
    rows = ["".join(top)]
    for i in range(height):
        half = int(i * slope)
        row = ["."] * width
        for x in range(peak - half, peak + half + 1):
            if i < snow_rows or (i == snow_rows and x % 2 == 0):
                row[x] = "V"
            else:
                row[x] = "N" if x <= peak else "n"
        row[peak - half - 1] = "K"
        row[peak + half + 1] = "K"
        rows.append("".join(row))
    return rows, peak


# ---------------------------------------------------------------- small icons

ICONS = {
    "chat": [
        "..KKKKKKKK..",
        ".KWWWWWWWWK.",
        "KWWWWWWWWWWK",
        "KWKWWKWWKWWK",
        "KWWWWWWWWWWK",
        ".KWWWWWWWWK.",
        "..KKWKKKKK..",
        "...KWK......",
        "...KK.......",
    ],
    "cap": [
        "....KKKK....",
        "..KKNNNNKK..",
        ".KNNNNNNNNK.",
        "KNNNNNNNNNNK",
        ".KKNNNNNNKK.",
        "...KNNNNK..K",
        "...KKKKKK..K",
        "..........KK",
    ],
    "terminal": [
        "KKKKKKKKKKKK",
        "KGGGGGGGGGGK",
        "KKKKKKKKKKKK",
        "KWWWWWWWWWWK",
        "KWKWWWWWWWWK",
        "KWWKWWWWWWWK",
        "KWKWWWWWWWWK",
        "KWWWWKKKKWWK",
        "KWWWWWWWWWWK",
        "KWWWWWWWWWWK",
        "KWWWWWWWWWWK",
        "KKKKKKKKKKKK",
    ],
    "server": [
        ".KKKKKKKKKK.",
        ".KNNNNNNNWK.",
        ".KKKKKKKKKK.",
        "............",
        ".KKKKKKKKKK.",
        ".KNNNNNNNWK.",
        ".KKKKKKKKKK.",
        "............",
        ".KKKKKKKKKK.",
        ".KNNNNNNNWK.",
        ".KKKKKKKKKK.",
        "............",
    ],
    "chip": [
        "...K..K..K..",
        "..KKKKKKKK..",
        "K.KNNNNNNK.K",
        "..KNWWWWNK..",
        "K.KNWWWWNK.K",
        "..KNWWWWNK..",
        "K.KNWWWWNK.K",
        "..KNNNNNNK..",
        "..KKKKKKKK..",
        "...K..K..K..",
    ],
    "paper": [
        ".KKKKKKK....",
        ".KWWWWWKK...",
        ".KWWWWWKWK..",
        ".KWKKKWKKKK.",
        ".KWWWWWWWWK.",
        ".KWKKKKKKWK.",
        ".KWWWWWWWWK.",
        ".KWKKKKKKWK.",
        ".KWWWWWWWWK.",
        ".KWKKKKWWWK.",
        ".KWWWWWWWWK.",
        ".KKKKKKKKKK.",
    ],
    "sun": [
        "....K....",
        ".K.....K.",
        "...KKK...",
        "..KYYYK..",
        "K.KYYYK.K",
        "..KYYYK..",
        "...KKK...",
        ".K.....K.",
        "....K....",
    ],
    "moon": [
        "...KKK...",
        ".KKYYK...",
        ".KYYK....",
        "KYYK.....",
        "KYYK.....",
        "KYYYK...K",
        ".KYYYKKKK",
        ".KKYYYYK.",
        "...KKKK..",
    ],
    "arrow": [
        "..KKK..",
        "..KKK..",
        "..KKK..",
        "KKKKKKK",
        ".KKKKK.",
        "..KKK..",
        "...K...",
    ],
    "family": [
        "..KKK.......",
        ".KSSSK......",
        ".KSSSK.KKK..",
        "..KKK.KSSSK.",
        ".KRRRKKSSSK.",
        "KRRRRRKKKK..",
        "KRRRRRKBBBK.",
        "KRRRRRKBBBBK",
        "KRRRRRKBBBBK",
        ".KKKKK.KKKK.",
    ],
    "football": [
        "...KKKKKK...",
        "..KWWKKWWK..",
        ".KWWWKKWWWK.",
        "KWKWWWWWWKWK",
        "KKKWWWWWWKKK",
        "KWWWWKKWWWWK",
        "KWWWKKKKWWWK",
        "KKWWWKKWWWKK",
        ".KKWWWWWWKK.",
        "..KWKWWKWK..",
        "...KKKKKK...",
    ],
    "golf": [
        "..KK........",
        "..KRRK......",
        "..KRRRRK....",
        "..KRRRRRK...",
        "..KRRRK.....",
        "..KK........",
        "..KK........",
        "..KK........",
        "..KK...KKK..",
        ".KTTKKKTWTK.",
        "KTTTTTTTTTTK",
        ".KKKKKKKKKK.",
    ],
    "gym": [
        "............",
        ".KK......KK.",
        "KNNK....KNNK",
        "KNNKKKKKKNNK",
        "KNNGGGGGGNNK",
        "KNNKKKKKKNNK",
        "KNNK....KNNK",
        ".KK......KK.",
    ],
    "gaming": [
        "..KKKKKKKK..",
        ".KNNNNNNNNK.",
        "KNNKNNNNXNNK",
        "KNKKKNNXNXNK",
        "KNNKNNNNXNNK",
        "KNNNNNNNNNNK",
        "KNNKKNNKKNNK",
        ".KKK.KK.KKK.",
    ],
    "hill": [
        ".....K......",
        "....KVK.....",
        "...KVVVK....",
        "..KNNNNnK.K.",
        ".KNNNNNnnKnK",
        "KNNNNNNnnnnK",
        "KTTTTTTTTTTK",
        "KKKKKKKKKKKK",
    ],
}


# ---------------------------------------------------------------- rendering

def paths(name, rows, ox=0, oy=0):
    width = len(rows[0])
    for number, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"{name}: row {number} is {len(row)} wide, expected {width}: {row!r}")

    runs = {}
    for y, row in enumerate(rows):
        x = 0
        while x < width:
            char = row[x]
            if char == ".":
                x += 1
                continue
            if char not in COLOURS:
                raise ValueError(f"{name}: unknown colour {char!r} in row {y}")
            start = x
            while x < width and row[x] == char:
                x += 1
            runs.setdefault(char, []).append(f"M{start + ox} {y + oy}h{x - start}v1h-{x - start}z")

    return "".join(f'<path class="c-{COLOURS[c]}" d="{"".join(d)}"/>' for c, d in runs.items())


def group(css_class, inner):
    return f'<g class="{css_class}">{inner}</g>'


def build_scene():
    parts = []
    left, left_peak = mountain(18, 0.8, 4)
    parts.append(paths("left mountain", left, -1 - len(left[0]), 75 - len(left)))

    right, right_peak = mountain(27, 0.72, 6)
    right_x, right_y = 35, 75 - len(right)
    parts.append(paths("right mountain", right, right_x, right_y))
    parts.append(group("flag", paths("flag", FLAG, right_x + right_peak, right_y - len(FLAG) + 1)))

    parts.append(paths("ground", ["T" * 130, "t" * 130], -45, 75))
    return "".join(parts)


def build_figure():
    sparks = "".join(
        group(f"spark spark-{i}", paths("spark", SPARK, x, y))
        for i, (x, y) in enumerate([(3, -3), (27, -6), (30, 4)], start=1)
    )
    dots = "".join(
        group(f"dot dot-{i}", paths("dot", ["KK"], x, 5))
        for i, x in enumerate([29, 32, 35], start=1)
    )
    return "".join([
        group("layer layer-scene", build_scene()),
        group("floor", paths("floor", FLOOR_SHADOW, 0, 75)),
        group("base", paths("eoin", EOIN)),
        group("eye-cover", paths("eye cover", BLINK, 12, 10)),
        group("eyes", paths("eyes", EYES, 12, 10)),
        group("blink", paths("blink", BLINK, 12, 10)),
        group("layer layer-brain", paths("brain", BRAIN, 9, 1) + sparks),
        group("layer layer-mouth",
              group("mouth-open", paths("mouth", MOUTH_OPEN, 14, 15))
              + group("speech", paths("speech", SPEECH, 26, 2))
              + dots),
        group("layer layer-heart",
              paths("heart window", HEART_WINDOW, 14, 25)
              + group("heart-beat", paths("heart", HEART, 14, 25))),
    ])


def build_blocks():
    blocks = {
        "figure": build_figure(),
        "sprite": (group("base", paths("eoin", EOIN))
                   + group("eye-cover", paths("eye cover", BLINK, 12, 10))
                   + group("eyes", paths("eyes", EYES, 12, 10))
                   + group("blink", paths("blink", BLINK, 12, 10))),
        "head": paths("head", EOIN[:21]),
    }
    for name, rows in ICONS.items():
        blocks[name] = paths(name, rows)
    return blocks


def write_favicon(head):
    style = "".join(f".c-{name}{{fill:{colour}}}" for name, colour in FAVICON_FILLS.items())
    FAVICON.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="3 -3 26 26" shape-rendering="crispEdges">'
        f"<style>{style}</style>"
        '<rect x="3" y="-3" width="26" height="26" rx="5" fill="#ffcf40"/>'
        f"{head}</svg>\n",
        encoding="utf-8",
    )
    print(f"updated {FAVICON.relative_to(ROOT)}")


def main():
    blocks = build_blocks()
    write_favicon(blocks["head"])
    for page in PAGES:
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        for name, svg in blocks.items():
            pattern = re.compile(r"(<!-- px:%s -->).*?(<!-- /px:%s -->)" % (name, name), re.S)
            text = pattern.sub(lambda m: m.group(1) + svg + m.group(2), text)
        page.write_text(text, encoding="utf-8")
        print(f"updated {page.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
