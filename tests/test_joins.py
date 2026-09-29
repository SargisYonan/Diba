"""Pass/fail tests for how the letters connect. Run with `make test`.

These fail only on things that break a join. Style questions (corners, near-miss
heights) are reported by `make qa` instead. To accept a join problem on purpose,
add "<glyph> join-top" (or join-bottom, join-gap) to qa/allow.txt.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "qa"))
from check import bar_metrics  # noqa: E402
from common import (LETTERS, Font, joins, joint_problems, label,  # noqa: E402
                    load_allow, seams, shape)

FONT = Font()
LETTER_GLYPHS = FONT.letters()
BAR = bar_metrics(FONT, LETTER_GLYPHS)
MID = (BAR[0] + BAR[1]) / 2
DRAWN = FONT.drawn_codepoints()
ALLOW = load_allow()

SIDES = [(g, side) for g in LETTER_GLYPHS
         for side, on in zip(("right", "left"), joins(g)) if on]


def allowed(glyph, check):
    return (glyph, check) in ALLOW or ("*", check) in ALLOW


@pytest.mark.parametrize("cp", [cp for cp in LETTERS if cp in DRAWN],
                         ids=lambda cp: LETTERS[cp][0])
def test_letter_has_every_form(cp):
    base = FONT.cmap[cp]
    forms = ["fina"] if LETTERS[cp][1] == "R" else ["init", "medi", "fina"]
    missing = [f for f in forms
               if f"{base}.{f}" not in FONT.glyphset or not FONT.glyph(f"{base}.{f}").polys]
    assert not missing, f"{LETTERS[cp][0]} has no {', '.join(missing)} form"


@pytest.mark.parametrize("glyph,side", SIDES, ids=[f"{g}-{s}" for g, s in SIDES])
def test_joint_matches_connecting_stroke(glyph, side):
    """Each joining edge must stand exactly on the connecting stroke, and the
    stroke must run flat into it. Stems, shoulders and tails that carry on
    past the stroke are fine."""
    problems = [msg for check, (_, size, msg) in
                joint_problems(FONT.glyph(glyph), side, BAR).items()
                if not allowed(glyph, check) and size >= (1 if check == "join-sag" else 0.5)]
    assert not problems, f"{label(glyph)}, {side} edge: " + "; ".join(problems)


@pytest.mark.parametrize("first", [cp for cp in DRAWN if LETTERS[cp][1] == "D"],
                         ids=lambda cp: LETTERS[cp][0])
def test_shaping_joins_every_following_letter(first):
    """A dual-joining letter followed by any letter must be shaped into two
    forms that both connect."""
    bad = []
    for second in DRAWN:
        run = shape(FONT.path, chr(first) + chr(second))
        found = seams(FONT, run, BAR)
        if len(found) != 1 or found[0]["mismatch"]:
            bad.append(f"{LETTERS[second][0]}: {' '.join(g for g, _, _ in run)}")
    assert not bad, "not joined as expected: " + "; ".join(bad)


@pytest.mark.parametrize("text,alaph", [
    ("ܐ", "uni0710"),                   # alone
    ("ܒܐ", "uni0710.fina"),        # joined, word-final
    ("ܒܐܒ", "uni0710.med2"),  # joined, mid-word
    ("ܘܐ", "uni0710.fin2"),        # after a non-joining letter
    ("ܕܐ", "uni0710.fin3"),        # after Dalath
    ("ܪܐ", "uni0710.fin3"),        # after Rish
], ids=["isolated", "final", "medial2", "final2", "final3-dalath", "final3-rish"])
def test_alaph_forms(text, alaph):
    names = [g for g, _, _ in shape(FONT.path, text)]
    assert alaph in names, f"expected {alaph}, got {names}"


@pytest.mark.parametrize("cp", [cp for cp in DRAWN if LETTERS[cp][1] == "R"],
                         ids=lambda cp: LETTERS[cp][0])
def test_right_joiner_never_joins_forward(cp):
    """Right-joining letters (Alaph, Dalath, Waw, ...) never connect to the
    letter after them, so between two Beths they must not take a form that
    joins on the left."""
    run = shape(FONT.path, "\u0712" + chr(cp) + "\u0712")
    mine = [g for g, _, _ in run if g.startswith(f"uni{cp:04X}")]
    assert mine and not joins(mine[0])[1], f"{LETTERS[cp][0]} shaped as {mine}"
