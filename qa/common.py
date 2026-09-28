"""Shared helpers for the Diba QA scripts.

Coordinates are font units (1000 per em). Syriac runs right to left, so a
glyph's RIGHT edge (x = advance width) meets the letter before it and its
LEFT edge (x = 0) meets the letter after it.
"""

import collections
import os
import re

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Set FONT=path/to/file.ttf to check a different build, e.g. one exported from Glyphs.
FONT = os.path.abspath(os.environ.get("FONT") or os.path.join(ROOT, "fonts", "Diba-Regular.ttf"))
SOURCE = os.path.join(ROOT, "sources", "Diba.glyphs")
OUT = os.path.join(ROOT, "out")
ALLOW = os.path.join(ROOT, "qa", "allow.txt")

# Unicode joining types: R joins only to the letter before it, D to both sides.
LETTERS = {
    0x0710: ("Alaph", "R"), 0x0712: ("Beth", "D"), 0x0713: ("Gamal", "D"),
    0x0714: ("Gamal Garshuni", "D"), 0x0715: ("Dalath", "R"),
    0x0716: ("Dotless Dalath Rish", "R"), 0x0717: ("He", "R"),
    0x0718: ("Waw", "R"), 0x0719: ("Zain", "R"), 0x071A: ("Heth", "D"),
    0x071B: ("Teth", "D"), 0x071C: ("Teth Garshuni", "D"),
    0x071D: ("Yudh", "D"), 0x071E: ("Yudh He", "R"), 0x071F: ("Kaph", "D"),
    0x0720: ("Lamadh", "D"), 0x0721: ("Mim", "D"), 0x0722: ("Nun", "D"),
    0x0723: ("Semkath", "D"), 0x0724: ("Final Semkath", "D"),
    0x0725: ("E", "D"), 0x0726: ("Pe", "D"), 0x0727: ("Reversed Pe", "D"),
    0x0728: ("Sadhe", "R"), 0x0729: ("Qaph", "D"), 0x072A: ("Rish", "R"),
    0x072B: ("Shin", "D"), 0x072C: ("Taw", "R"),
}

# Which sides each positional form connects on: (right, left).
# Alaph's extra forms: med2 is joined to the letter before but not word-final;
# fin2 and fin3 are unjoined word-final Alaphs.
FORMS = {
    "": (False, False), "init": (False, True), "medi": (True, True),
    "fina": (True, False), "med2": (True, False),
    "fin2": (False, False), "fin3": (False, False),
}
FORM_NAMES = {
    "": "isolated", "init": "initial", "medi": "medial", "fina": "final",
    "med2": "medial 2", "fin2": "final 2", "fin3": "final 3",
}

STEPS = 32  # segments per curve when flattening


def split_name(glyph):
    """'uni0712.init' -> (0x0712, 'init'); None for anything not a letter."""
    m = re.fullmatch(r"uni(07[12][0-9A-F])(?:\.(\w+))?", glyph)
    if not m or int(m.group(1), 16) not in LETTERS:
        return None
    return int(m.group(1), 16), m.group(2) or ""


def label(glyph):
    parts = split_name(glyph)
    if not parts:
        return glyph
    cp, form = parts
    return f"{LETTERS[cp][0]} {FORM_NAMES.get(form, form)}"


def joins(glyph):
    """(joins_right, joins_left) for a letter glyph."""
    return FORMS.get(split_name(glyph)[1], (False, False))


class FlattenPen(BasePen):
    """Collects each contour as a polygon, approximating curves by lines."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.polys, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, a, b, c):
        x0, y0 = self.cur[-1]
        for i in range(1, STEPS + 1):
            t = i / STEPS
            u = 1 - t
            self.cur.append((
                u**3 * x0 + 3 * u * u * t * a[0] + 3 * u * t * t * b[0] + t**3 * c[0],
                u**3 * y0 + 3 * u * u * t * a[1] + 3 * u * t * t * b[1] + t**3 * c[1],
            ))

    def _qCurveToOne(self, a, b):
        x0, y0 = self.cur[-1]
        for i in range(1, STEPS + 1):
            t = i / STEPS
            u = 1 - t
            self.cur.append((
                u * u * x0 + 2 * u * t * a[0] + t * t * b[0],
                u * u * y0 + 2 * u * t * a[1] + t * t * b[1],
            ))

    def _closePath(self):
        if self.cur:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath


class Glyph:
    def __init__(self, name, width, polys):
        self.name, self.width, self.polys = name, width, polys
        xs = [x for p in polys for x, _ in p]
        ys = [y for p in polys for _, y in p]
        self.bounds = (min(xs), min(ys), max(xs), max(ys)) if xs else None

    def ink_at_x(self, x):
        """Vertical runs of ink [(bottom, top), ...] along the line at x."""
        ys = []
        for poly in self.polys:
            n = len(poly)
            for i in range(n):
                (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
                if (x0 <= x < x1) or (x1 <= x < x0):
                    ys.append(y0 + (x - x0) * (y1 - y0) / (x1 - x0))
        ys.sort()
        return [(ys[i], ys[i + 1]) for i in range(0, len(ys) - 1, 2)]

    def contains(self, x, y):
        """Whether (x, y) is inside the ink (even-odd; the font has no overlaps)."""
        return sum(b <= y <= t for b, t in self.ink_at_x(x)) % 2 == 1

    def ink_at_y(self, y):
        """Horizontal runs of ink [(left, right), ...] along the line at y."""
        xs = []
        for poly in self.polys:
            n = len(poly)
            for i in range(n):
                (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


class Font:
    def __init__(self, path=FONT):
        if not os.path.exists(path):
            raise SystemExit(f"{path} not found - run `make build` first")
        self.path = path
        self.tt = TTFont(path)
        self.glyphset = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self._cache = {}

    def glyph(self, name):
        if name not in self._cache:
            pen = FlattenPen(self.glyphset)
            self.glyphset[name].draw(pen)
            self._cache[name] = Glyph(name, self.tt["hmtx"][name][0], pen.polys)
        return self._cache[name]

    def letters(self):
        """Every letter glyph in the font that has outlines, in glyph order."""
        return [g for g in self.tt.getGlyphOrder()
                if split_name(g) and self.glyph(g).polys]

    def drawn_codepoints(self):
        return sorted(cp for cp in LETTERS
                      if cp in self.cmap and self.glyph(self.cmap[cp]).polys)


def run_at(runs, y):
    """The (bottom, top) run that contains y, or None."""
    for b, t in runs:
        if b <= y <= t:
            return b, t
    return None


def mode(values):
    return collections.Counter(values).most_common(1)[0][0] if values else None


def load_allow():
    """Lines of qa/allow.txt as a set of (glyph, check) pairs."""
    allowed = set()
    if os.path.exists(ALLOW):
        for line in open(ALLOW, encoding="utf-8"):
            line = line.split("#", 1)[0].split()
            if len(line) >= 2:
                allowed.add((line[0], line[1]))
    return allowed


# --- joints -------------------------------------------------------------------

STEM = 40   # a joint this much taller/deeper than the bar is a stem, not a step
PROBE = 1   # measure joints this far inside the edge


def edge_run(glyph, side, mid):
    """The run of ink at the joining height just inside one edge, or None."""
    x = glyph.width - PROBE if side == "right" else PROBE
    return run_at(glyph.ink_at_x(x), mid)


def compare_seam(left, right, bar):
    """Problems where `left`'s right edge meets `right`'s left edge.

    Returns [(y, message)]. Heights that run on past the stroke (a stem going
    up, a tail going down) are allowed to differ; everything else must line up.
    """
    bottom, top = bar
    mid = (bottom + top) / 2
    a, b = edge_run(left, "right", mid), edge_run(right, "left", mid)
    if a is None or b is None:
        who = left.name if a is None else right.name
        return [(mid, f"{who} does not reach the joint")]
    out = []
    if a[0] > bottom - STEM and b[0] > bottom - STEM and abs(a[0] - b[0]) >= 0.5:
        out.append((min(a[0], b[0]), f"bottoms differ: {a[0]:.0f} vs {b[0]:.0f}"))
    if a[1] < top + STEM and b[1] < top + STEM and abs(a[1] - b[1]) >= 0.5:
        out.append((max(a[1], b[1]), f"tops differ: {a[1]:.0f} vs {b[1]:.0f}"))
    return out


def shape(path, text):
    """HarfBuzz output as [(glyph, x, y)] in visual (left-to-right) order."""
    import uharfbuzz as hb
    blob = hb.Blob.from_file_path(path)
    hbfont = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf)
    names = [hbfont.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    out, x = [], 0
    for name, pos in zip(names, buf.glyph_positions):
        out.append((name, x + pos.x_offset, pos.y_offset))
        x += pos.x_advance
    return out


def seams(font, run, bar):
    """Every joint in a shaped run, as dicts: x, glyphs, problems, and
    `mismatch` when only one side of it is shaped to join."""
    letters = [(g, x) for g, x, _ in run if split_name(g)]
    out = []
    for (lg, lx), (rg, rx) in zip(letters, letters[1:]):
        l_joins, r_joins = joins(lg)[0], joins(rg)[1]
        if not (l_joins or r_joins):
            continue
        seam = dict(x=rx, left=lg, right=rg, problems=[], mismatch=l_joins != r_joins)
        if seam["mismatch"]:
            seam["problems"].append(((bar[0] + bar[1]) / 2,
                                     "only one side is shaped to join"))
        else:
            seam["problems"] = compare_seam(font.glyph(lg), font.glyph(rg), bar)
        out.append(seam)
    return out
