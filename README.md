# Ganta

An East Syriac (Madnḥaya) typeface, digitised from a mid-20th-century
catalogue of Assyrian types.

The repository is set up so that **the only manual work is drawing**. The glyph
inventory, every positional variant, the mark anchors and the whole OpenType
layer — joining, the four Alaph forms, obligatory ligatures, vowel splitting,
mark and mark-to-mark attachment — are generated and already verified against
HarfBuzz.

## Status

The source is a complete skeleton: 221 correctly named, encoded and anchored
glyphs with no outlines yet. It compiles, and all 29 shaping cases pass, so the
logic is known-good before a single curve is drawn.

## Procedure

### 1. Get the scans in

Three kinds of page, kept apart because they are used differently:

    reference/scans/raw/       whole pages as scanned — flattened by make dewarp
    reference/scans/charts/    alphabet charts — sliced into sorts
    reference/scans/samples/   text settings   — never sliced, used for fitting

Put the **whole page** into `raw/`, not a crop you have straightened by hand:
cropping around a chart by eye adds its own rotation, and the dewarper fits
better with every row of type on the page available to it.

The catalogue prints the alphabet twice, solid and as an outline drawing. Slice
both, but **trace from the outline**: it is the intended contour, while the
solid impression carries ink spread and records the press rather than the
design. Use the solid chart to check weight once your outlines are filled, and
the text samples to judge spacing.

### 2. Flatten the pages

    make dewarp

A page in a bound book does not merely sit crooked, it curves, and no rotation
can undo that. Results go to `reference/scans/charts/`.

How it works, because each part earns its keep:

* **Baselines are sampled along the feet of the sorts**, not once per sort. Each
  sort contributes every column that stands on its own resting level, which
  turns eight measurements per row into several hundred. Sorts whose foot is a
  slope rather than a flat contribute nothing, and descenders are dropped.
* **The rows are pooled to find the warp they share.** One row can only show a
  tilt and a gentle bend; paper does more than that. But it does the same thing
  to every row, so pooling measures the same distortion several times over and
  the shape lifts out of the noise. On the supplied charts the rows agreed with
  each other to *r = 0.93* — that is the sheet, not the letters.
* **It runs until it stops gaining**, and never keeps a pass that made the page
  worse. If nothing beats the original, it says so and writes it unchanged.
* Rows with only a handful of sorts borrow the shape the well-populated rows
  agree on rather than inventing a slope from a cluster, and no curve is
  extrapolated past the last sort it was fitted from.
* **Two models are tried and the flatter one kept.** *Flexible* lets each row
  bend on its own; *rigid* holds every row to one shape for the whole sheet and
  lets them differ only in height. Neither wins everywhere — on these two charts
  they win one apiece — so `--mode auto` (the default) measures both.

Measured on the supplied charts:

| | bow before | bow after | model chosen | worst row tilt |
|---|---|---|---|---|
| outline chart | 14.2 px | **2.4 px** | rigid | 6.9° → 0.7° |
| solid chart | 7.9 px | **2.0 px** | flexible | 4.5° → 1.1° |

It writes `<name>_baselines.png` alongside, drawing the curve fitted to each
row. Look at it: if a baseline is wrong the flattening will be too.

`--passes` caps the iterations, `--degree` how far a row may bend, `--mode`
forces one of the two models, and `--no-pool` fits each row alone. It corrects vertical bowing, not perspective,
so shoot the page square-on.

**Resolution matters more than any of this.** Below roughly 60px per sort the
feet cannot be located reliably — outline strokes go sub-pixel and break apart —
and `make dewarp` will warn you. It is also far too coarse to trace from. The
crops in this project run about 90px per sort and flatten well.

### 3. Cut the pages into sorts

    make slice

This straightens the page (`--deskew`, since these are book scans), then finds
the ink by projection profile and writes one PNG per cell into
`reference/glyphs/`, numbered right-to-left within each row (`--rtl`, since a
Syriac chart reads that way). It also writes:

* `reference/glyphs/index.html` — a contact sheet showing every cell with its id
* `reference/mapping.json` — a stub, cell id → glyph name, for you to fill in

* `reference/glyphs/<page>_deskewed.png` — the straightened page, so you can
  check the correction was sane

If cells run together or a letter splits in two, adjust `--gap` and
`--threshold` and re-run.

**On skew.** Two corrections happen automatically. The page as a whole is
levelled (the supplied charts needed −4.91° and −2.86°). Then, because a book
page curls rather than merely sitting crooked, each row is measured again on
its own and straightened separately — the supplied outline chart still ran from
+0.86° in row 1 to −2.08° in row 4 after the global fix. A row is only
corrected when its top and bottom edges agree about the tilt to within 1.5°;
otherwise the letters are leading the measurement rather than the page, and the
row is left alone. `--no-row-deskew` turns the second pass off.

What is left after that is **not** a scan artefact and should not be corrected.
These charts are hand-inked construction drawings: letter to letter, the
bottom edges scatter by several degrees, which is an order of magnitude more
than the residual warp. That is the draughtsman's hand, and it is the source
material. You are drawing clean outlines over these as templates, not
inheriting their wobble — and if one template sits visibly off, a background
image can be nudged or rotated per layer inside Glyphs.

### 4. Name the sorts and straighten them

    make adjust

The contact sheet is an editor, not just a listing. Each sort sits on a grid you
can turn on and size, with centre guides, and per-sort controls for **tilt**,
**skew** and **size** — arrow keys for tilt and size, `,`/`.` for skew, hold
shift for coarse steps, `n`/`p` to walk through them. Type the glyph name into
the box under each one.

Automatic correction levels the page and its rows; it cannot judge one letter
against another on a hand-inked chart, which is what this is for.

**Save adjustments.json** writes `reference/adjustments.json` (a real save in
Chrome, a download elsewhere — move it into `reference/` if so). Names go into
`reference/mapping.json`:

    { "page84_001": "uni0710", "page84_002": "uni0710.fina", ... }

Names follow the inventory in `scripts/syriac_data.py` — `uni0712` for
isolated Beth, `uni0712.init` / `.medi` / `.fina` for its joined forms. A
catalogue usually prints all four forms of the dual-joining letters, which is
exactly what the font needs.

Both files survive re-slicing, so you can go back and forth.

### 5. Set the metrics before you draw

    make measure

This reads the baseline, body height, ascent and descent straight off the chart
and prints a block of constants for `scripts/syriac_data.py`. Paste them in and
re-run `make skeleton`. Doing this after you have started drawing means
redrawing, which is why it gets its own step.

Measured from the supplied chart: body height 86.5px, ascent 0.40× body,
descent 0.36× body, stroke weight roughly 0.32× body. Those are already in
`syriac_data.py`, with the body height mapped to a round 500 units.

One caveat, also carried in the code: the deepest thing below the chart's
baseline is Dalath's dot, not a descender. The chart has no deep final forms and
no vowels hanging below the line, so `DESCENDER` will want to go lower once
those exist.

### 6. Put the references into the source

    make place

Each mapped image becomes the background image of that glyph's layer, at one
uniform scale across the whole specimen so relative proportions survive, sitting
on the baseline. Anything you corrected in the contact sheet is baked into a
copy under `reference/glyphs/adjusted/` — the cut taken from the scan is never
written over. `make place --clear` takes them out again.

### 6b. Auto-trace, to start from shapes rather than a blank layer

    make trace CHART=solid_overview

This places the templates and traces each sort into outlines on the layer, at
the same scale and offset as its template, so the drawing lands exactly on the
picture it came from.

The face is built from straight cuts and sharp corners, so it is traced as
**polygons**: walk the boundary between ink and paper, then simplify the
staircase back into the straight edges it came from. A curve fitter would round
off the corners that are the whole character of the type. Twenty-seven sorts
come out at about 19 nodes each.

Specks in the impression and pinholes in the ink are dropped by area, measured
as a fraction of each sort's own inked area rather than in pixels, so the same
settings hold whatever size the scan is. Counters survive; dirt does not.

`--tolerance` sets how tightly the polygon follows the scan (default 1.5 scan
pixels; lower is tighter and gives more nodes). Glyphs that already have
outlines are left alone unless you pass `OVERWRITE=1`, so this cannot eat work
you have done by hand.

Trace from the **solid** chart: it is already a filled shape. The outline chart
is a line drawing, so tracing it would give you the stroke of the pen rather
than the letter. Keep the outline chart as the reference for what the shape is
meant to be.

What comes out is a starting point, not a finished letter. The printed sorts are
not perfectly square and neither is the tracing, so expect to straighten edges
and align stems by hand.

### 7. Draw

    make open

Draw over the templates in Glyphs. Work in this order — it front-loads the
decisions everything else inherits:

1. **Beth, Mim, Lamadh, Nun, Alaph.** These fix the body height, the stroke
   weight, the join height and the descender depth. Everything else is measured
   against them.
2. The rest of the isolated letters.
3. The `.init` / `.medi` / `.fina` variants. **A catalogue prints one sort per
   letter, so most of these are not in it** — the supplied chart has only four
   (`uni0721.medi`, `uni0722.medi`, `uni0722.fina`, `uni071F.fina`). The rest
   you derive: take the isolated form and add or remove the connecting stroke.
   The join has to land at exactly the same height in every letter or words
   will look broken, so set that height once and hold it.
4. Marks. Draw them centred on the origin: the anchors do the positioning.
5. The ligature sorts (`uni0720uni0710.*`, `uni072Cuni0710.*`,
   `uni072Auni0308.*`, `uni0716uni0308.*`).

Check the inventory has not drifted at any point:

    make inventory

### 8. Build and check

    make build     # fonts/Ganta-Regular.ttf and .otf
    make test      # the shaping suite
    make proof     # out/proof.html
    make check     # fontbakery

`make proof` is the one to keep open next to the scan — it is HTML, so the
browser runs the real Syriac shaper and shows what applications will do.

## What is already wired up

| Feature | What it does |
|---|---|
| `init` `medi` `fina` | The joined forms of the 16 dual-joining letters |
| `fin2` `fin3` `med2` | Alaph's Syriac-specific forms (see below) |
| `ccmp` | Splits dotted Ptakha (U+0732) into an above and a below dot so each half reaches its own anchor |
| `rlig` | Lamadh-Alaph, Taw-Alaph, and Rish/Dotless-Dalath + Syame as single sorts |
| `stch` | Expands the Abbreviation Mark (U+070F) into a rule that stretches over the abbreviated letters |
| `mark` `mkmk` | Vowel placement and mark stacking, generated from the anchors |
| `calt` | Empty, reserved for Phase 2 (see below) |

### Alaph

HarfBuzz chooses between four shapes; the font only has to supply each one.
Verified empirically, recorded in the shaping suite:

* `.fina` — after a letter that joins to the left (a dual-joiner in init/medi)
* `.fin3` — after the Dalath/Rish group: Dalath, Dotless Dalath Rish, Rish
* `.fin2` — after any other letter that does not join to the left
* `.med2` — when Alaph falls inside a word rather than at its end

### Phase 2: contextual alternates

Noto Sans Syriac Eastern carries a further layer this skeleton deliberately
leaves out — narrow and wide variants (`.N`, `.W`) and descender-avoidance forms
(`.QR`, used before Qaph and Rish), selected by chained contextual lookups in
`calt`. That refinement is worth adding once the base shapes are settled and you
can see where the collisions actually are. There is a worked pattern in the
`calt` section of `scripts/make_skeleton.py`.

## Layout

    sources/Ganta.glyphs      the typeface source
    scripts/syriac_data.py    glyph inventory, metrics, joining classes -- edit this
    scripts/make_skeleton.py  turns the inventory into the Glyphs source
    scripts/dewarp.py         flattens the curl out of a scanned page
    scripts/slice_specimen.py cuts charts into per-sort images
    scripts/contact_sheet.py  builds the naming and straightening editor
    scripts/adjust.py         the per-sort tilt/skew/size transform
    scripts/measure_specimen.py reads the vertical metrics off a chart
    scripts/place_references.py  sets those images as tracing templates
    scripts/shape_test.py     runs the shaping suite
    scripts/proof.py          writes the HTML proof
    qa/shaping_tests/         the shaping expectations
    reference/scans/raw/      whole pages as scanned
    reference/scans/charts/   alphabet charts, sliced
    reference/scans/samples/  text settings, for judging fit
    reference/glyphs/         sliced cells and the contact sheet
    reference/mapping.json    cell id -> glyph name
    reference/adjustments.json  per-cell tilt/skew/size corrections

`scripts/syriac_data.py` is the single source of truth. Change the inventory or
the metrics there, not in the Glyphs file.

## Regenerating the source

`make skeleton` refuses to overwrite an existing source, because it would
discard your drawing. Once you have started, use `make inventory` to see what
has drifted and add glyphs in Glyphs by hand.

## Expected fontbakery results while drawing

`make check` will report empty-glyph failures, a blank `.notdef`, and
`usWinAscent`/`usWinDescent` "too large" until there are outlines to measure
against. These clear themselves as you draw. Hinting (`prep` table) is a release
step, not something to chase now.

## Prior art in this project

* `/Users/sargis/Projects/NohadraSyriac` — the previous font, and where the
  Lamadh-Alaph and Taw-Alaph ligature logic and the Abbreviation Mark treatment
  come from.
* `/Users/sargis/Projects/syriac` — Noto Sans Syriac, the reference for the
  contextual-alternate layer and the shaping-test format.

## Scope

Garshuni is out of scope. That means both the Arabic vowel marks and the two
Garshuni letters, U+0714 Gamal Garshuni and U+071C Teth Garshuni, are absent.
Those two are ordinary dual-joining Syriac letters and could be re-added in a
line of `scripts/syriac_data.py` if the scope ever changes.

`--full` adds the Persian and Sogdian letters (U+072D–072F, U+074D–074F). They
are not in the catalogue either; the flag exists only to round out Syriac block
coverage if that ever becomes worth having.

## Licence

SIL Open Font License 1.1, see `OFL.txt`.
# DibaSyriac
