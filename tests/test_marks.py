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
from common import SOURCE, Font, label, shape, split_name  # noqa: E402

FONT = Font()
SRC = glyphsLib.GSFont(SOURCE)
ANCHORS = {g.name: {a.name: (a.position.x, a.position.y) for a in g.layers[0].anchors}
           for g in SRC.glyphs}
LETTERS = FONT.letters()
MARKS = {name: a for name, a in ANCHORS.items() if "_top" in a or "_bottom" in a}
REACH = 80   # a mark spans about this far either side of its anchor


@pytest.mark.parametrize("glyph", LETTERS)
def test_letter_has_top_and_bottom(glyph):
    assert set(ANCHORS[glyph]) == {"top", "bottom"}, \
        f"{label(glyph)} has anchors {sorted(ANCHORS[glyph])}, expected top and bottom"


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
    allowed = {"top", "bottom", "_top", "_bottom"}
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
