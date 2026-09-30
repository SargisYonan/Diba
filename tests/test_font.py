"""Pass/fail tests for the font as a whole. Run with `make test`."""

import os
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "qa"))
from common import Font  # noqa: E402

FONT = Font()
# Characters that are meant to draw nothing.
INVISIBLE = {0x0000, 0x000D, 0x0020, 0x00A0, 0x200C, 0x200D, 0x200E, 0x200F}


def test_no_character_draws_nothing():
    """Every character the font claims must have an outline. An empty glyph
    makes the character vanish; leaving it out (Export unticked in Glyphs)
    lets apps borrow it from another font instead."""
    empty = [f"U+{cp:04X} {unicodedata.name(chr(cp), '?').title()} ({g})"
             for cp, g in sorted(FONT.cmap.items())
             if cp not in INVISIBLE and not FONT.glyph(g).polys]
    assert not empty, "these characters draw nothing: " + "; ".join(empty)


def test_notdef_is_visible():
    assert FONT.glyph(".notdef").polys, ".notdef must be drawn, so missing characters show"
