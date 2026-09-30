"""Pass/fail tests for mark anchors. Run with `make test`.

Letters carry `top` and `bottom`; marks above the line carry `_top` (where
they attach) and `top` (where the next mark stacks); marks below carry
`_bottom` and `bottom`; a mark with parts on both sides carries all four. The mark and mkmk features are generated from these
anchors, so the last test checks the built font actually follows them.
"""

import os
import sys

import glyphsLib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "qa"))
from common import (LETTER_ONLY_ANCHORS, MARK_TOUCH, SOURCE, Font, bases_for,  # noqa: E402
                    clearance, drawn_marks,
                    label, load_allow, load_anchors, mark_collisions, neighbour_texts, place_mark,
                    shape, split_name)

FONT = Font()
SRC = glyphsLib.GSFont(SOURCE)
ANCHORS = {g.name: {a.name: (a.position.x, a.position.y) for a in g.layers[0].anchors}
           for g in SRC.glyphs}
LETTERS = FONT.letters()
MARKS = {name: a for name, a in ANCHORS.items() if "_top" in a or "_bottom" in a}
REACH = 80   # a mark spans about this far either side of its anchor
DRAWN = drawn_marks(FONT, load_anchors())
ALLOW = load_allow()


@pytest.mark.parametrize("glyph", LETTERS)
def test_letter_has_top_and_bottom(glyph):
    names = set(ANCHORS[glyph])
    assert {"top", "bottom"} <= names and names - {"top", "bottom"} <= LETTER_ONLY_ANCHORS, \
        f"{label(glyph)} has anchors {sorted(names)}, expected top and bottom"


@pytest.mark.parametrize("glyph", LETTERS)
def test_letter_anchors_clear_the_ink(glyph):
    """Marks must not land on the letter: `top` above everything under it,
    `bottom` below everything over it."""
    g = FONT.glyph(glyph)
    (tx, ty), (bx, by) = ANCHORS[glyph]["top"], ANCHORS[glyph]["bottom"]
    assert 0 <= tx <= g.width, f"top anchor x={tx} is outside the letter"
    assert 0 <= bx <= g.width, f"bottom anchor x={bx} is outside the letter"
    over = [t for dx in range(-REACH, REACH + 1, 4) for _, t in g.ink_at_x(tx + dx + 0.5)]
    under = [b for dx in range(-REACH, REACH + 1, 4) for b, _ in g.ink_at_x(bx + dx + 0.5)]
    assert not over or ty > max(over), f"top anchor y={ty} is inside the ink (reaches {max(over):.0f})"
    assert not under or by < min(under), f"bottom anchor y={by} is inside the ink (reaches {min(under):.0f})"


@pytest.mark.parametrize("mark", sorted(MARKS))
def test_mark_anchors(mark):
    """Each side a mark attaches on needs its stacking anchor too. Marks with
    parts both above and below (like U+0732) carry both pairs."""
    names = set(MARKS[mark])
    assert names in ({"_top", "top"}, {"_bottom", "bottom"},
                     {"_top", "top", "_bottom", "bottom"}), \
        f"{mark} has anchors {sorted(names)}"


def test_no_stray_anchor_names():
    allowed = {"top", "bottom", "_top", "_bottom"} | LETTER_ONLY_ANCHORS | \
        {"_" + a for a in LETTER_ONLY_ANCHORS}
    odd = {f"{g}: {n}" for g, a in ANCHORS.items() for n in a if n not in allowed}
    assert not odd, "unexpected anchors: " + ", ".join(sorted(odd))


@pytest.mark.parametrize("glyph", [g for g in LETTERS if "." not in g])
def test_marks_attach_at_anchors(glyph):
    """Shaping a letter with a mark above and one below must put each mark at
    the letter's anchor. Fails if a hand-written mark feature overrides them."""
    cp = split_name(glyph)[0]
    for mark, base_anchor, mark_anchor in (("ܵ", "top", "_top"), ("ܼ", "bottom", "_bottom")):
        run = shape(FONT.path, chr(cp) + mark)
        mark_glyph = f"uni{ord(mark):04X}"
        (_, mx, my), = [r for r in run if r[0] == mark_glyph]
        (_, bx, by), = [r for r in run if r[0] == glyph]
        want = (bx + ANCHORS[glyph][base_anchor][0] - ANCHORS[mark_glyph][mark_anchor][0],
                by + ANCHORS[glyph][base_anchor][1] - ANCHORS[mark_glyph][mark_anchor][1])
        assert (mx, my) == want, f"{mark_glyph} on {label(glyph)} at {(mx, my)}, anchors say {want}"


def test_every_drawn_mark_attaches():
    """A mark with outlines but no attaching anchor is drawn wherever the pen
    happens to be, beside the letter instead of on it."""
    gdef = FONT.tt["GDEF"].table.GlyphClassDef.classDefs
    loose = [g for g, cls in gdef.items() if cls == 3 and FONT.glyph(g).polys
             and not any(a.startswith("_") for a in ANCHORS.get(g, {}))]
    assert not loose, "marks with no attaching anchor: " + ", ".join(sorted(loose))


@pytest.mark.parametrize("mark", sorted(DRAWN))
def test_mark_sits_on_its_anchors(mark):
    """An above mark rises from its `_top` and its `top` clears it; a below
    mark hangs from its `_bottom` and its `bottom` is under it."""
    _, y0, _, y1 = FONT.glyph(mark).bounds
    a = ANCHORS[mark]
    if "_top" in a:
        assert y0 >= a["_top"][1] - 5, f"ink dips to y={y0:.0f}, below _top at {a['_top'][1]}"
        assert a["top"][1] > y1, f"top anchor y={a['top'][1]} is inside the ink (to {y1:.0f})"
    else:
        assert y1 <= a["_bottom"][1] + 5, f"ink rises to y={y1:.0f}, above _bottom at {a['_bottom'][1]}"
        assert a["bottom"][1] < y0, f"bottom anchor y={a['bottom'][1]} is inside the ink (to {y0:.0f})"


@pytest.mark.parametrize("mark", sorted(DRAWN))
def test_mark_clears_every_letter(mark):
    """Placed by the anchors, the mark must not touch any form of any letter."""
    bad = []
    for glyph in bases_for(mark, LETTERS):
        x, y = place_mark(ANCHORS, glyph, mark, DRAWN[mark])
        d = clearance(FONT.glyph(mark), x, y, FONT.glyph(glyph), 0, 0)
        if d is not None and d < MARK_TOUCH:
            bad.append(f"{label(glyph)} ({d:.0f})")
    assert not bad, f"{mark} touches: " + ", ".join(bad)


@pytest.mark.parametrize("mark", sorted(m for m in DRAWN if "." not in m))
def test_mark_clears_neighbours(mark):
    """In shaped text, a mark must not run into the letters beside its own,
    on any form of any letter next to any other letter."""
    bad = set()
    for text in neighbour_texts(FONT, chr(int(mark[3:7], 16))):
        for _, _, _, other, d in mark_collisions(FONT, shape(FONT.path, text)):
            if d < MARK_TOUCH and not (other, "mark-neighbour") in ALLOW:
                bad.add(f"{text} hits {label(other)} ({d:.0f})")
    assert not bad, f"{mark}: " + "; ".join(sorted(bad))


@pytest.mark.parametrize("kind", ["top", "bottom"])
def test_marks_stack(kind):
    """Two marks on the same side stack without touching."""
    side = [m for m, (base, _) in DRAWN.items() if base == kind]
    bad = []
    for first in side:
        for second in side:
            x, y = place_mark(ANCHORS, first, second, DRAWN[second])
            d = clearance(FONT.glyph(second), x, y, FONT.glyph(first), 0, 0)
            if d is not None and d < MARK_TOUCH:
                bad.append(f"{second} on {first} ({d:.0f})")
    assert not bad, "; ".join(bad)


@pytest.mark.parametrize("text,mark,base", [
    ("\u0726\u032E", "uni032E.pe", "uni0726"),
    ("\u0712\u0726\u032E\u0712", "uni032E.pe", "uni0726.medi"),
])
def test_semicircle_touches_pe(text, mark, base):
    """The semicircle under Pe is swapped for a copy whose tips meet Pe's
    bottom edge, just overlapping it so no hairline gap shows."""
    run = shape(FONT.path, text)
    names = [g for g, _, _ in run]
    assert mark in names, f"got {names}"
    (_, mx, my), = [r for r in run if r[0] == mark]
    (_, bx, by), = [r for r in run if r[0] == base]
    d = clearance(FONT.glyph(mark), mx, my, FONT.glyph(base), bx, by)
    assert d is not None and -5 <= d <= 0, f"semicircle is {d} from Pe, should touch"


@pytest.mark.parametrize("text,base", [("\u0713\u0330", "uni0713"),
                                       ("\u0712\u0713\u0330\u0712", "uni0713.medi")])
def test_majlyana_under_gamal_stroke(text, base):
    """The majlyana under Gamal sits under the flat stroke at its bottom left,
    not under the tail."""
    run = shape(FONT.path, text)
    names = [g for g, _, _ in run]
    assert "uni0330.gamal" in names, f"got {names}"
    (_, mx, _), = [r for r in run if r[0] == "uni0330.gamal"]
    (_, bx, _), = [r for r in run if r[0] == base]
    g = FONT.glyph(base)
    flat = [s for s in g.ink_at_y(-5)]            # the tail is the only ink below the baseline
    tail_left = min(s[0] for s in flat)
    centre = mx - bx + sum(FONT.glyph("uni0330.gamal").bounds[0::2]) / 2
    assert centre < tail_left, f"majlyana centre x={centre:.0f} is over the tail (starts {tail_left:.0f})"
    d = clearance(FONT.glyph("uni0330.gamal"), mx, [r for r in run if r[0] == "uni0330.gamal"][0][2], g, bx, 0)
    assert d is not None and d >= 30, f"majlyana comes within {d:.0f} units of Gamal's tail"
