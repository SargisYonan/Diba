"""Pass/fail tests for the shapes of the letters. Run with `make test`.

Most outline questions are judged by `make qa` against what the other letters
do. The rules here are ones the design follows everywhere, so they are tested
outright. A glyph excused in qa/allow.txt ("<glyph> inner-corner") is skipped.
"""

import os
import sys

import glyphsLib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "qa"))
from check import bar_metrics, corners, source_letters  # noqa: E402
from common import SOURCE, Font, is_allowed, label, load_allow  # noqa: E402

FONT = Font()
LETTERS = list(source_letters(glyphsLib.GSFont(SOURCE), set(FONT.letters())))
BAR_TOP = bar_metrics(FONT, FONT.letters())[1]
ALLOW = load_allow()


@pytest.mark.parametrize("glyph,layer", LETTERS, ids=[g for g, _ in LETTERS])
def test_inner_top_right_corners_are_rounded(glyph, layer):
    """Inside corners at the top right of a counter (the white space under an
    arm, opening toward the bottom left), above the connecting stroke, are
    rounded rather than sharp."""
    if is_allowed(ALLOW, glyph, "inner-corner"):
        pytest.skip(f"{glyph} is excused in qa/allow.txt")
    sharp = [(round(c["x"]), round(c["y"])) for c in corners(glyph, layer, FONT.glyph(glyph))
             if not c["convex"] and (c["vert"], c["horiz"]) == ("bottom", "left")
             and c["y"] > BAR_TOP and c["radius"] < 2]
    assert not sharp, f"{label(glyph)}: sharp inner top-right corner at {sharp}"
