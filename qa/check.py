"""Checks the letters of Diba for joining and outline problems.

    python qa/check.py            report everything
    python qa/check.py --strict   exit 1 if there are errors (used by make test)

Joins are measured on the built font (fonts/Diba-Regular.ttf), which is what
applications see. Corners and alignment are measured on the Glyphs source,
which is what you edit. Every problem is written to out/qa.json as well, for
qa/proof.py to draw on the proof sheet.

Silence something you meant to do by adding "<glyph> <check>" to qa/allow.txt.
"""

import argparse
import collections
import json
import math
import os
import sys

import glyphsLib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (LETTERS, OUT, PROBE, SOURCE, STEM, Font, joins,  # noqa: E402
                    label, load_allow, mode, run_at, split_name)

DEEP = 20          # ...and again this far in, to see if the bar bends near the joint
OVERHANG = 10      # ink this far past the advance width is flagged
NEAR_LEVEL = 15    # a flat edge this close to a common height is flagged
SLANT = 4          # a line this close to flat/upright is flagged
CORNER_SLACK = 3   # rounding this far from the usual radius is flagged

SEVERITY = {"error": 0, "warning": 1, "info": 2}


class Report:
    def __init__(self, allowed):
        self.items, self.allowed, self.silenced = [], allowed, 0

    def add(self, severity, check, glyph, message, x=None, y=None):
        if (glyph, check) in self.allowed or ("*", check) in self.allowed:
            self.silenced += 1
            return
        self.items.append(dict(severity=severity, check=check, glyph=glyph,
                               label=label(glyph), message=message,
                               x=None if x is None else round(x),
                               y=None if y is None else round(y)))


def r1(v):
    return round(v, 1) if abs(v - round(v)) > 0.05 else int(round(v))


# --- joins ------------------------------------------------------------------

def bar_metrics(font, letters):
    """The height of the connecting stroke, taken from what most joints do."""
    bottoms, tops = [], []
    for g in letters:
        glyph = font.glyph(g)
        for side, on in zip(("right", "left"), joins(g)):
            if on:
                x = glyph.width - PROBE if side == "right" else PROBE
                runs = glyph.ink_at_x(x)
                if runs:
                    bottoms.append(round(runs[0][0]))
                    short = [t for b, t in runs if t < 400]
                    if short:
                        tops.append(round(short[0]))
    return mode(bottoms), mode(tops)


def check_joins(font, letters, report):
    bottom, top = bar_metrics(font, letters)
    mid = (bottom + top) / 2
    overlap = {"left": [], "right": []}

    for g in letters:
        glyph = font.glyph(g)
        w = glyph.width
        for side, on in zip(("right", "left"), joins(g)):
            edge = w if side == "right" else 0
            inward = -1 if side == "right" else 1
            runs = glyph.ink_at_x(edge + inward * PROBE)
            run = run_at(runs, mid)
            where = "right edge (joins the letter before)" if side == "right" \
                else "left edge (joins the letter after)"

            if not on:
                # A flat, full-height cut on a side that never joins reads as
                # a broken join.
                if run and abs(run[0] - bottom) < 1 and abs(run[1] - top) < 1:
                    report.add("warning", "stub", g,
                               f"{where.split(' (')[0]} never joins, but ends in a flat "
                               f"cut the full height of the connecting stroke "
                               f"({r1(run[0])}–{r1(run[1])}), so it looks like "
                               f"a join with nothing attached", edge, mid)
                continue

            if run is None:
                for d in range(PROBE, w):
                    if run_at(glyph.ink_at_x(edge + inward * d), mid):
                        report.add("error", "join-gap", g,
                                   f"{where}: the connecting stroke stops {d} units "
                                   f"short of the edge, leaving a gap",
                                   edge + inward * d, mid)
                        break
                else:
                    near = ", ".join(f"{r1(b)}–{r1(t)}" for b, t in runs) or "nothing"
                    report.add("error", "join-gap", g,
                               f"{where}: nothing at the height of the connecting "
                               f"stroke ({bottom}–{top}); ink at the edge: {near}",
                               edge, mid)
                continue

            b, t = run
            if b > bottom - STEM and abs(b - bottom) >= 0.5:
                d = b - bottom
                report.add("error" if abs(d) > 2 else "warning", "join-bottom", g,
                           f"{where}: bottom of the join is at y={r1(b)}, "
                           f"{r1(abs(d))} units {'above' if d > 0 else 'below'} "
                           f"the baseline of the connecting stroke (y={bottom})",
                           edge, b)
            if t < top + STEM and abs(t - top) >= 0.5:
                d = t - top
                report.add("error" if abs(d) > 2 else "warning", "join-top", g,
                           f"{where}: top of the join is at y={r1(t)}, "
                           f"{r1(abs(d))} units {'higher' if d > 0 else 'lower'} "
                           f"than the connecting stroke (y={top}), making a step",
                           edge, t)

            deep = run_at(glyph.ink_at_x(edge + inward * DEEP), mid)
            # A top that rises just inside the edge is the fillet into the
            # letter's body; a bottom that moves, or a top that drops, is a
            # stroke that is sloped or pinched at the joint.
            if deep and b > bottom - STEM and t < top + STEM and (
                    abs(deep[0] - b) >= 1 or deep[1] - t <= -1):
                report.add("warning", "join-bend", g,
                           f"{where}: the stroke changes height right before the join "
                           f"({r1(deep[0])}–{r1(deep[1])} at {DEEP} units in, "
                           f"{r1(b)}–{r1(t)} at the edge)", edge + inward * DEEP, deep[1])

            spans = [s for s in glyph.ink_at_y(mid)]
            reach = min(s[0] for s in spans) if side == "left" else max(s[1] for s in spans)
            overlap[side].append((g, reach - edge))

    for side, rows in overlap.items():
        usual = mode([round(o) for _, o in rows])
        for g, o in rows:
            if round(o) != usual:
                report.add("info", "join-overlap", g,
                           f"{side} joint pokes {r1(abs(o))} units "
                           f"{'past' if (o < 0) == (side == 'left') else 'short of'} the edge; "
                           f"most {side} joints use {usual}",
                           (0 if side == "left" else font.glyph(g).width) + o, (bottom + top) / 2)
    return bottom, top


def check_overhang(font, letters, report):
    for g in letters:
        glyph = font.glyph(g)
        x0, y0, x1, y1 = glyph.bounds
        if x1 > glyph.width + OVERHANG:
            ys = [y for p in glyph.polys for x, y in p if x == x1]
            report.add("warning", "overhang", g,
                       f"ink reaches x={r1(x1)}, {r1(x1 - glyph.width)} units past the "
                       f"right edge, under or into the letter before", x1, ys[0])
        if x0 < -OVERHANG:
            ys = [y for p in glyph.polys for x, y in p if x == x0]
            report.add("warning", "overhang", g,
                       f"ink reaches x={r1(x0)}, {r1(-x0)} units past the left "
                       f"edge, under or into the letter after", x0, ys[0])


# --- outlines (from the source) ----------------------------------------------

def segments(path):
    """[(start_node, [following nodes up to and including the next on-curve])]"""
    nodes = list(path.nodes)
    on = [i for i, n in enumerate(nodes) if n.type != "offcurve"]
    out = []
    for k, i in enumerate(on):
        j = on[(k + 1) % len(on)]
        pts, m = [], i
        while True:
            m = (m + 1) % len(nodes)
            pts.append(nodes[m])
            if m == j:
                break
        out.append((nodes[i], pts))
    return out


def source_letters(font_source, built):
    for g in font_source.glyphs:
        if g.export and g.name in built:
            yield g, g.layers[0]


def check_outlines(source, font, report):
    letters = list(source_letters(source, set(font.letters())))

    # Heights that many flat edges share (baseline, top of the stroke, ...).
    flat = collections.Counter()
    users = collections.defaultdict(set)
    for g, layer in letters:
        for path in layer.paths:
            for a, pts in segments(path):
                b = pts[-1]
                if len(pts) == 1 and a.position.y == b.position.y and \
                        abs(a.position.x - b.position.x) >= 20:
                    flat[a.position.y] += 1
                    users[a.position.y].add(g.name)
    levels = sorted(y for y, n in flat.items() if n >= 6 and len(users[y]) >= 3)

    mixed = []
    for g, layer in letters:
        kinds = {n.type for p in layer.paths for n in p.nodes}
        if "qcurve" in kinds and "curve" in kinds:
            mixed.append(g.name)
        for path in layer.paths:
            if not path.closed:
                x, y = path.nodes[0].position.x, path.nodes[0].position.y
                if len(path.nodes) == 1:
                    report.add("warning", "stray-point", g.name,
                               f"a lone point at ({r1(x)},{r1(y)}) that belongs to no "
                               f"outline; select it and delete it", x, y)
                else:
                    report.add("error", "open-path", g.name,
                               f"outline starting at ({r1(x)},{r1(y)}) is not closed, "
                               f"so it will not be filled", x, y)
            for a, pts in segments(path):
                if len(pts) != 1:
                    continue
                (x0, y0), (x1, y1) = (a.position.x, a.position.y), \
                    (pts[0].position.x, pts[0].position.y)
                dx, dy = abs(x1 - x0), abs(y1 - y0)
                if 0 < dy <= SLANT and dx >= 20:
                    report.add("warning", "slanted-line", g.name,
                               f"line from ({r1(x0)},{r1(y0)}) to ({r1(x1)},{r1(y1)}) "
                               f"is {r1(dy)} units off flat", (x0 + x1) / 2, (y0 + y1) / 2)
                elif 0 < dx <= SLANT and dy >= 20:
                    report.add("warning", "slanted-line", g.name,
                               f"line from ({r1(x0)},{r1(y0)}) to ({r1(x1)},{r1(y1)}) "
                               f"is {r1(dx)} units off upright", (x0 + x1) / 2, (y0 + y1) / 2)
                elif dy == 0 and dx >= 20 and y0 not in levels:
                    near = [lv for lv in levels if 0 < abs(lv - y0) <= NEAR_LEVEL]
                    if near:
                        lv = min(near, key=lambda v: abs(v - y0))
                        report.add("warning", "off-level", g.name,
                                   f"flat edge at y={r1(y0)} is {r1(abs(y0 - lv))} units "
                                   f"{'above' if y0 > lv else 'below'} the common height "
                                   f"y={r1(lv)} ({flat[lv]} edges use it)",
                                   (x0 + x1) / 2, y0)

    if mixed:
        report.add("info", "mixed-curves", "*",
                   f"{len(mixed)} letters mix quadratic (TrueType) and cubic curves in "
                   f"one outline. Glyphs exports this fine, but other tools choke on it. "
                   f"To tidy: select all, Paths > Other > Convert to Cubic. "
                   f"Letters: {', '.join(mixed)}")

    check_corners(letters, levels, report, font)
    return levels


def corners(g, layer, ink):
    """Every roughly square corner in the glyph: rounded (a curve between two
    lines) or sharp (two lines). `ink` is the built glyph, used to tell outer
    corners from inside ones."""
    width = layer.width
    right_join, left_join = joins(g.name)
    for path in layer.paths:
        segs = segments(path)
        n = len(segs)
        for k, (a, pts) in enumerate(segs):
            prev, nxt = segs[k - 1], segs[(k + 1) % n]
            if len(pts) == 1 and len(nxt[1]) == 1:
                p0, p2 = a.position, nxt[1][0].position
                c = (pts[0].position.x, pts[0].position.y)
                rad, radii, chord = 0, (0, 0), None
            elif len(pts) > 1 and len(prev[1]) == 1 and len(nxt[1]) == 1:
                p0, s, e, p2 = prev[0].position, a.position, pts[-1].position, \
                    nxt[1][0].position
                d1 = (s.x - p0.x, s.y - p0.y)
                d2 = (p2.x - e.x, p2.y - e.y)
                den = d1[0] * d2[1] - d1[1] * d2[0]
                if den == 0:
                    continue
                t = ((e.x - s.x) * d2[1] - (e.y - s.y) * d2[0]) / den
                c = (s.x + t * d1[0], s.y + t * d1[1])
                radii = (math.hypot(c[0] - s.x, c[1] - s.y),
                         math.hypot(c[0] - e.x, c[1] - e.y))
                rad = sum(radii) / 2
                chord = ((s.x + e.x) / 2, (s.y + e.y) / 2)
            else:
                continue
            d1 = (c[0] - p0.x, c[1] - p0.y)
            d2 = (p2.x - c[0], p2.y - c[1])
            l1, l2 = math.hypot(*d1), math.hypot(*d2)
            if not l1 or not l2:
                continue
            u1, u2 = (d1[0] / l1, d1[1] / l1), (d2[0] / l2, d2[1] / l2)
            angle = math.degrees(math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1]))))
            if not 70 < angle < 110:
                continue

            if chord and rad >= 2:
                # A rounded outer corner cuts its tip away, leaving the virtual
                # corner outside the ink; an inside fillet fills it in.
                convex = not ink.contains(*c)
                v = (c[0] - chord[0], c[1] - chord[1])
                out = v if convex else (-v[0], -v[1])
            else:
                # Sharp: an outer corner has ink in one of the four diagonal
                # directions around it, an inside corner in three.
                diag = [(dx, dy) for dx in (-1, 1) for dy in (-1, 1)]
                inside = [d for d in diag if ink.contains(c[0] + 3 * d[0], c[1] + 3 * d[1])]
                if len(inside) == 1:
                    convex, out = True, (-inside[0][0], -inside[0][1])
                elif len(inside) == 3:
                    convex = False
                    out = next(d for d in diag if d not in inside)
                else:
                    continue
            # Cut ends of joining strokes are square by design.
            if rad == 0 and ((right_join and abs(c[0] - width) <= 2) or
                             (left_join and c[0] <= 2)):
                continue
            yield dict(x=c[0], y=c[1], radius=rad, radii=radii, convex=convex,
                       vert="top" if out[1] > 0 else "bottom",
                       horiz="right" if out[0] > 0 else "left")


def check_corners(letters, levels, report, font):
    groups = collections.defaultdict(list)
    for g, layer in letters:
        for c in corners(g, layer, font.glyph(g.name)):
            near = [lv for lv in levels if abs(lv - c["y"]) <= NEAR_LEVEL]
            level = min(near, key=lambda v: abs(v - c["y"])) if near else None
            key = (c["convex"], c["vert"], c["horiz"], level)
            groups[key].append((g.name, c))

    for (convex, vert, horiz, level), rows in groups.items():
        if len(rows) < 4:
            continue
        usual = mode([round(c["radius"]) for _, c in rows])
        agree = sum(abs(c["radius"] - usual) <= CORNER_SLACK for _, c in rows)
        if agree < len(rows) * 2 / 3:
            continue  # no clear convention here
        kind = (f"outer {vert}-{horiz} corner" if convex else
                f"inside corner (opening {vert}-{horiz})") + \
            (f" at y≈{level}" if level is not None else "")
        for g, c in rows:
            rad = c["radius"]
            if abs(rad - usual) > CORNER_SLACK:
                what = "is sharp" if rad == 0 else f"has radius {r1(rad)}"
                report.add("warning", "corner", g,
                           f"{kind} {what}; {agree} of {len(rows)} like it use "
                           f"radius {usual}", c["x"], c["y"])
            elif rad and abs(c["radii"][0] - c["radii"][1]) > 5:
                report.add("info", "corner-uneven", g,
                           f"{kind} is lopsided: {r1(c['radii'][0])} on one side, "
                           f"{r1(c['radii'][1])} on the other", c["x"], c["y"])


# --- coverage -----------------------------------------------------------------

def check_coverage(font, report):
    for cp, (name, jt) in LETTERS.items():
        base = font.cmap.get(cp)
        if not base or not font.glyph(base).polys:
            report.add("info", "missing", f"uni{cp:04X}",
                       f"{name} (U+{cp:04X}) is not drawn")
            continue
        wanted = ["fina"] if jt == "R" else ["init", "medi", "fina"]
        for form in wanted:
            g = f"{base}.{form}"
            if g not in font.glyphset or not font.glyph(g).polys:
                report.add("error", "missing", g, f"{name} has no {form} form")


# --- output -------------------------------------------------------------------

COLOURS = {"error": "\033[31m", "warning": "\033[33m", "info": "\033[36m"}


def print_report(report, levels, bar):
    tty = sys.stdout.isatty()

    def c(sev, text):
        return f"{COLOURS[sev]}{text}\033[0m" if tty else text

    print(f"Connecting stroke: y={bar[0]} to y={bar[1]}")
    print(f"Common heights of flat edges: {', '.join(str(r1(v)) for v in levels)}\n")

    by_glyph = collections.defaultdict(list)
    for item in report.items:
        by_glyph[item["glyph"]].append(item)

    def order(g):
        parts = split_name(g)
        return parts if parts else (0, g)

    for g in sorted(by_glyph, key=order):
        items = sorted(by_glyph[g], key=lambda i: SEVERITY[i["severity"]])
        print("Whole font" if g == "*" else f"{label(g)}  [{g}]")
        for i in items:
            print(f"  {c(i['severity'], i['severity'].upper()):<8} {i['check']:<13} {i['message']}")
        print()

    counts = collections.Counter(i["severity"] for i in report.items)
    print(", ".join(c(s, f"{counts[s]} {s}{'s' if counts[s] != 1 else ''}")
                    for s in SEVERITY) +
          (f", {report.silenced} silenced by qa/allow.txt" if report.silenced else ""))
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 if there are errors")
    ap.add_argument("--quiet", action="store_true", help="only write out/qa.json")
    args = ap.parse_args()

    font = Font()
    source = glyphsLib.GSFont(SOURCE)
    letters = font.letters()
    report = Report(load_allow())

    check_coverage(font, report)
    bar = check_joins(font, letters, report)
    check_overhang(font, letters, report)
    levels = check_outlines(source, font, report)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "qa.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(bar=bar, levels=levels, items=report.items), fh,
                  ensure_ascii=False, indent=1)

    if args.quiet:
        counts = collections.Counter(i["severity"] for i in report.items)
    else:
        counts = print_report(report, levels, bar)
    if args.strict and counts["error"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
