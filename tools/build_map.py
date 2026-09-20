#!/usr/bin/env python3
"""Turn a world-atlas TopoJSON file into the pixel grids the travel map draws.

Download countries-50m.json from the world-atlas package (Natural Earth data, public
domain), then:

    python3 tools/build_map.py path/to/countries-50m.json

Writes assets/js/world-pixels.js with a world view and a closer Europe view.
The TopoJSON file itself isn't needed by the site.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "js" / "world-pixels.js"

# Degrees per pixel. Europe uses wider longitude steps so the continent isn't stretched sideways.
VIEWS = {
    "world": {"west": -180.0, "north": 84.0, "cols": 240, "rows": 95, "dlon": 1.5, "dlat": 1.5},
    "europe": {"west": -25.0, "north": 72.0, "cols": 88, "rows": 76, "dlon": 0.8, "dlat": 0.5},
}

# Countries whose far-away territories shouldn't light up with the mainland.
# Shapes centred outside this box (west, east, south, north) become "<name> (overseas)".
HOME = {
    "France": (-10.0, 20.0, 35.0, 55.0),
}


def decode_arcs(topo):
    scale = topo["transform"]["scale"]
    translate = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append((x * scale[0] + translate[0], y * scale[1] + translate[1]))
        arcs.append(points)
    return arcs


def ring_points(ring, arcs):
    points = []
    for index in ring:
        arc = arcs[index] if index >= 0 else list(reversed(arcs[~index]))
        points.extend(arc if not points else arc[1:])
    return points


def unwrap(ring):
    """Make rings that cross the 180 degree line continuous (Russia and Fiji do)."""
    out = [ring[0]]
    offset = 0.0
    for (x0, _), (x1, y1) in zip(ring, ring[1:]):
        if x1 - x0 > 180:
            offset -= 360
        elif x1 - x0 < -180:
            offset += 360
        out.append((x1 + offset, y1))
    return out


def polygons(geometry, arcs):
    if geometry["type"] == "Polygon":
        shapes = [geometry["arcs"]]
    elif geometry["type"] == "MultiPolygon":
        shapes = geometry["arcs"]
    else:
        return []
    return [[unwrap(ring_points(ring, arcs)) for ring in shape] for shape in shapes]


def inside(x, y, ring):
    hit = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def country_at(lon, lat, shapes):
    for candidate in (lon, lon + 360, lon - 360):
        for index, polygon, (x0, y0, x1, y1) in shapes:
            if not (x0 <= candidate <= x1 and y0 <= lat <= y1):
                continue
            if inside(candidate, lat, polygon[0]) and not any(inside(candidate, lat, hole) for hole in polygon[1:]):
                return index
    return -1


def rasterise(view, shapes, name_count):
    cols, rows = view["cols"], view["rows"]
    grid = [[-1] * cols for _ in range(rows)]
    counts = [0] * name_count

    for row in range(rows):
        lat = view["north"] - (row + 0.5) * view["dlat"]
        for col in range(cols):
            lon = view["west"] + (col + 0.5) * view["dlon"]
            index = country_at(lon, lat, shapes)
            if index >= 0:
                grid[row][col] = index
                counts[index] += 1

    # Countries too small to own a whole pixel still get one, at the middle of their largest shape.
    by_size = sorted(shapes, key=lambda s: -(s[2][2] - s[2][0]) * (s[2][3] - s[2][1]))
    for index, _, (x0, y0, x1, y1) in by_size:
        if counts[index]:
            continue
        lon = (x0 + x1) / 2
        if lon > 180:
            lon -= 360
        col = int((lon - view["west"]) / view["dlon"])
        row = int((view["north"] - (y0 + y1) / 2) / view["dlat"])
        if 0 <= row < rows and 0 <= col < cols:
            grid[row][col] = index
            counts[index] += 1

    runs_by_row = []
    for row in grid:
        runs = []
        col = 0
        while col < cols:
            value = row[col]
            start = col
            while col < cols and row[col] == value:
                col += 1
            if value >= 0:
                runs.extend([start, col - start, value])
        runs_by_row.append(runs)
    return {"w": cols, "h": rows, "rows": runs_by_row}


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    topo = json.loads(pathlib.Path(sys.argv[1]).read_text())
    arcs = decode_arcs(topo)

    names = []
    shapes = []

    def name_index(name):
        if name not in names:
            names.append(name)
        return names.index(name)

    for geometry in topo["objects"]["countries"]["geometries"]:
        name = geometry.get("properties", {}).get("name")
        if not geometry.get("arcs") or not name or name == "Antarctica":
            continue
        index = name_index(name)
        for polygon in polygons(geometry, arcs):
            box = bbox(polygon[0])
            owner = index
            if name in HOME:
                west, east, south, north = HOME[name]
                x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                if not (west <= x <= east and south <= y <= north):
                    owner = name_index(name + " (overseas)")
            shapes.append((owner, polygon, box))

    data = {"names": names, "views": {}}
    for key, view in VIEWS.items():
        data["views"][key] = rasterise(view, shapes, len(names))
        print(f"{key}: {view['cols']}x{view['rows']}")

    OUT.write_text(
        "// Generated by tools/build_map.py from Natural Earth data (public domain). Don't edit by hand.\n"
        "window.EK_WORLD = " + json.dumps(data, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)}: {len(names)} countries, {OUT.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
