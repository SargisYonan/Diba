# Changelog

## 2026-09-30: more marks, Pe semicircle, Gamal majlyana

**New marks, turned on.** For each, the attaching anchor stays where the mark
was drawn, and the stacking anchor sits 50 units beyond its ink.

| Glyph | Mark | Change |
|---|---|---|
| `uni0304` | macron above | `top` 780 → 743. Floats 100 above its anchor, like the oblique line |
| `uni0307` | dot above | `top` 780 → 768 |
| `uni0320` | minus below | Removed a stray `_top` and `top`: a below-mark with `_top` would also have attached above the letter. `bottom` → −222 |
| `uni0323` | dot below | `bottom` → −226 |
| `uni0324` | diaeresis below | `bottom` → −226 |
| `uni0331` | macron below | `bottom` → −222 |

**Macron above on isolated Kaph.** Handled like the oblique line: a raised
copy, `uni0304.kaph` (110 units higher), is swapped in by the Kaph lookup
(`SUB_10`), which now covers both marks.

**Semicircle under Pe.** The semicircle (U+032E) now touches Pe's bottom edge,
overlapping by 2 units so no hairline gap shows. Pe's four forms have a
`semicircle` anchor at y=2, and `uni032E.pe` attaches there by
`_semicircle`. The swap is done by lookup `SUB_11` in `rlig`. Other marks
under Pe, such as the rukkakha dot, still use `bottom` and keep their gap.

**Majlyana under Gamal.** Gamal's four forms have their own `majlyana` anchor,
separate from the other diacritics. It sits 50 units under the flat
bottom-left stroke, left of the curl of the tail: x=205 in the isolated and
final forms, x=132 in initial and medial. `uni0330.gamal` attaches there by
`_majlyana`, swapped in by lookup `SUB_12`. A vowel below Gamal still uses
`bottom`. A vowel typed after the majlyana stacks under it.

**Checks.** Letters may carry `majlyana` and `semicircle` besides `top` and
`bottom`. Every mark needs an attaching anchor of some kind. New tests check
that the semicircle touches Pe and that the majlyana clears Gamal's tail by at
least 30.

**Open: three marks to redraw narrower.** Minus below (`uni0320`), macron below
(`uni0331`) and diaeresis below (`uni0324`) cross the tails that Kaph, Teth,
Sadhe, Gamal and final Nun sweep under the letter before them, by up to 126
units. At their current heights they clear everything at about **290 wide**
(x ±145) for the two bars, and **287 wide** (x ±144) for the diaeresis. Their
tests fail until then.

## 2026-09-29: new glyphs from Glyphs

Six glyphs drawn in Glyphs, turned back on and fitted to the rest of the font.
QA: 0 errors, 1 warning. Tests: 421 pass.

| Glyph | What it is | Change |
|---|---|---|
| `uni070A` | Syriac contraction | Export on. Already spaced like the other punctuation (82 left, 30 right) |
| `uni0711` | Superscript Alaph | Export on. `_top` 530 → 542 (its ink starts there); `top` 780 → 813 |
| `uni0747` | Oblique line above | Export on. `top` 780 → 742. `_top` left at 530: the line floats 99 units up as drawn, which keeps it clear of the letters beside it |
| `uni0303` | Tilde above | Export on. `_top` 530 → 431, where its ink starts; at 530 it sank 99 units into the letter. `top` → 680 |
| `uni032E` | Breve below | Export on. Anchors were at x=158 though the breve is centred on 0; `_bottom` (158,−22) → (0,0), `bottom` → (0,−215) |
| `uni0330` | Tilde below | Export on. `_bottom` −22 → 62, where its ink ends; it rose 84 units into the letter. `bottom` → −187 |

Letter anchors moved so the wider new marks clear every letter and neighbour
by at least 30 units, while keeping 50 from their own letter:

| Glyph | Anchor | Before | After | Why |
|---|---|---|---|---|
| `uni071B` `uni071B.fina` Teth isolated/final | bottom | (264,−228) | (184,−228) | The breve reached Teth's tail |
| `uni071B.init` `uni071B.medi` Teth initial/medial | bottom | (182,−228) | (142,−298) | The same, balanced against the tails of Nun, Teth and Sadhe that sweep under Teth from the next letter |
| `uni0722.fina` Nun final | bottom | (177,−320) | (97,−320) | The breve reached Nun's tail |

**Oblique line on isolated Kaph.** The line is 562 wide and Kaph is short, so
over isolated Kaph it reached into the tall letter before it (up to 76 units
of overlap, e.g. ܕܟ݇). A raised copy, `uni0747.kaph` (`_top` 420, so 110 units
higher), is swapped in by a new `rlig` lookup (`SUB_10`), only when the line
sits on isolated Kaph. The lookup skips any other vowel in between. Everywhere
else the line is unchanged.

**Remaining warning:** a breve under Zain comes within 23 units of an isolated
Kaph beside it (ܙ̮ܟ). Close, but not touching.

**Tests and proofs.** New `tests/test_font.py` fails if any character in the
font draws nothing, or if `.notdef` is blank. `tests/test_joins.py` checks the
Kaph swap. The proof page has a *Punctuation and signs* section: every drawn
non-letter, every mark on a dotted circle, and punctuated text.
`proof-text.png` shows the punctuation and `proof-vowels.png` shows every mark.

## 2026-09-29: release fixes

A full check of the font (`make all`, fontbakery `check-universal`, and a
comparison of HarfBuzz against macOS CoreText) and the fixes that came out of
it. Before/after images: `out/release-diff.png` (run `make all` to rebuild).

**Result:** QA 0 errors, 0 warnings, 0 notes. 396 tests pass. Fontbakery
went from 5 failures and 1 warning to 0 failures and 1 warning; the warning is
the dotted circle having 8 dots where many fonts use 12 or 16, which is a style
choice. CoreText and HarfBuzz produce identical glyphs and positions for all 98
test texts, covering vowelled words, the Lord's Prayer, the Alaph forms, Rish
with syame and the kerned pairs.

### New outlines, built only from shapes already in the font

The punctuation uses the syame's dot, so it matches the letters. Punctuation
side bearings are 82 on the left, the same as the gap between letters, and 30
on the right.

| Glyph | What it is |
|---|---|
| `.notdef` | Hollow box, so missing characters show instead of vanishing |
| `uni0640` tatweel | The connecting stroke (y 0–209), width 200 |
| `period` | One dot on the baseline |
| `colon` | Two dots, baseline to letter height (500) |
| `uni0700` | Syriac end of paragraph: four dots in a diamond |
| `uni0701` | Supralinear full stop: one dot at letter height |
| `uni0702` | Sublinear full stop: one dot below the baseline |
| `uni0705` | Horizontal colon: two dots side by side at mid-height |
| `uni25CC` | Dotted circle: eight small dots on a ring |

### Hidden until drawn (Export unticked)

These characters drew nothing, which made them vanish from text. Hidden, they
fall back to another font instead. To bring one back, draw it and tick Export
in Glyphs.

- Punctuation: `exclam` `parenleft` `parenright` `bracketleft` `bracketright`
  `guillemotleft` `guillemotright` `asterisk` `plus` `minus` `equal` `slash`
  `backslash` `hyphen` `degree` `ellipsis`
- Arabic punctuation: `uni060C` `uni061B` `uni061F`
- Digits: `zero`–`nine`, `uni0660`–`uni066C`
- Syriac punctuation whose shape is more than plain dots, or whose arrangement
  I was not sure of: `uni0703` `uni0704` `uni0706`–`uni070D`
- Superscript Alaph `uni0711`, and the crosses `uni2670` `uni2671`
- Undrawn marks: `uni0730` `uni0731` `uni0733` `uni0734` `uni0736` `uni0737`
  `uni073A` `uni073B` `uni073D` `uni073E` `uni0740` `uni0743` `uni0744`
  `uni0745` `uni0746` `uni0747` `uni0748` `uni0749` `uni074A`, and the
  combining marks `uni0303`
  `uni0304` `uni0307` `uni030A` `uni0320` `uni0323` `uni0324` `uni0325`
  `uni032D` `uni032E` `uni0330` `uni0331`

Still exported: the abbreviation mark `uni070F` and its parts `SAMin`
`SAMline` `SAMdot` `SAMout`, which the `stch` feature needs. `uni070F` has
since been drawn; the `SAM` parts are still empty.

### Vertical metrics

| Value | Before | After | Why |
|---|---|---|---|
| typo / hhea ascender | 750 | 960 | Clears the highest single vowel (Zqapa over Rish with syame, 959) |
| typo / hhea descender | −350 | −560 | Clears the lowest single vowel (under Sadhe, −555) |
| winAscent / winDescent | 750 / 557 | 1240 / 840 | Windows clips at these, so it covers two stacked vowels |
| Use Typo Metrics | off | on | Every platform uses the same line spacing |

The default line height grows from 1100 to 1520, so vowelled lines no longer
collide. Unvowelled text also gets the taller line height; to tighten it, lower
the ascender and descender, keeping in mind where vowels reach.

### Anchors

| Glyph | Anchor | Before | After |
|---|---|---|---|
| `uni071F` Kaph isolated | top y | 287 | 321 (Zqapa was 16 units from the enlarged Kaph) |
| `uni0728` Sadhe isolated | bottom y | −326 | −353 (vowels were 23 units from the deeper belly) |
| `uni0728.fina` Sadhe final | bottom y | −323 | −353 (was 20 units away) |

Every vowel now keeps at least 50 units from its letter, as on the other
letters.

### Outlines

- `uni0728.fina` Sadhe final: straightened an edge that was 4 units off
  upright, (571,−74) → (575,−74).
- **All curves converted to cubic.** 123 outlines had 419 quadratic
  (TrueType) points mixed with cubic ones. Quadratic curves convert to cubic
  exactly: a pixel comparison of every glyph before and after shows no
  difference. Ten points marked as curves but with no handles, really straight
  lines, are now marked as line points.

### Metadata

- `fsType` 8 (editable embedding) → 0 (installable), as usual for OFL fonts.
- License URL (name ID 14) → https://openfontlicense.org.
- Unicode ranges: added Latin-1 (no-break space) and Geometric Shapes (dotted
  circle).
- Vendor ID: set to `YONN` in Glyphs (was `NONE`).

### Build and QA

- `make build` now runs `scripts/fix_hinting.py`, which adds a `prep` table
  with smart dropout control and a `gasp` table (what `gftools
  fix-nonhinting` does). ttfautohint can't hint Syriac, so the font ships
  unhinted; this keeps thin strokes from dropping out on Windows at small
  sizes.
- `qa/check.py` corner check: it now treats a run of curves between two
  straight edges as one corner. Converted TrueType corners are drawn as two
  cubic curves, and the old check skipped them. That coverage turned up two
  deliberate shapes, which are now in `qa/allow.txt`: Alaph's long curve from
  the diagonal into the bottom stroke, and the rounded tip of Dalath's and
  Rish's slanted end.
- `qa/allow.txt`: Yudh He (U+071E) marked as not needed, like the Garshuni
  letters and Reversed Pe.
