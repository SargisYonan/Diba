# Ganta -- an East Syriac typeface digitised from a mid-20th-century catalogue.

PY       := venv/bin/python
SOURCE   := sources/Ganta.glyphs
FAMILY   := Ganta
FONTS    := fonts
FONT     := $(FONTS)/Ganta-Regular.ttf
# Glyph charts get sliced into sorts. Text samples in reference/scans/samples/
# are for judging fit and spacing and are deliberately not sliced.
# _baselines.png files are dewarp's own diagnostics, not charts to slice.
SCANS    := $(filter-out %_baselines.png,$(wildcard reference/scans/charts/*.png \
              reference/scans/charts/*.tif reference/scans/charts/*.jpg))
RAW      := $(wildcard reference/scans/raw/*.png reference/scans/raw/*.tif reference/scans/raw/*.jpg)

.DEFAULT_GOAL := help

help:
	@echo "Ganta build targets"
	@echo
	@echo "  make venv       install the Python toolchain into venv/"
	@echo "  make skeleton   (re)generate $(SOURCE) from the glyph inventory"
	@echo "  make inventory  list glyphs the source is missing vs. the inventory"
	@echo "  make dewarp     flatten raw book pages into reference/scans/charts/"
	@echo "  make slice      cut the charts into per-sort images"
	@echo "  make adjust     open the contact sheet to name and straighten sorts"
	@echo "  make measure    read the vertical metrics off the chart"
	@echo "  make place      set those images as tracing templates in the source"
	@echo "  make trace      place them and auto-trace the sorts into outlines"
	@echo "  make open       open the source in Glyphs 3"
	@echo "  make build      compile $(FONTS)/*.ttf and *.otf"
	@echo "  make test       run the shaping suite against the built font"
	@echo "  make check      run fontbakery"
	@echo "  make proof      write out/proof.html"
	@echo "  make all        build + test + proof"

venv: venv/.stamp
venv/.stamp: requirements.txt
	python3 -m venv venv
	venv/bin/pip install -q --upgrade pip
	venv/bin/pip install -q -r requirements.txt
	touch $@

# Bootstrap only. Refuses to clobber a source you have started drawing in;
# use `make inventory` to compare instead.
skeleton: venv
	$(PY) scripts/make_skeleton.py

inventory: venv
	$(PY) scripts/make_skeleton.py --check $(SOURCE)

# Flatten the curl out of raw book pages before anything else touches them.
dewarp: venv
	@test -n "$(RAW)" || { echo "no pages in reference/scans/raw/"; exit 1; }
	@mkdir -p reference/scans/charts
	@for p in $(RAW); do \
	  $(PY) scripts/dewarp.py "$$p" --debug \
	    -o "reference/scans/charts/$$(basename $${p%.*}).png"; \
	done

# Rebuild the contact sheet from the cells already cut, leaving their
# numbering alone -- your names are attached to those numbers.
sheet: venv
	$(PY) scripts/slice_specimen.py --sheet-only

adjust: sheet
	open reference/glyphs/index.html

slice: venv
	@test -n "$(SCANS)" || { echo "no charts in reference/scans/charts/"; exit 1; }
	$(PY) scripts/slice_specimen.py $(SCANS) --rtl --deskew --save-deskewed

measure: venv
	$(PY) scripts/measure_specimen.py reference/scans/charts/outline_overview.png \
	  --weight-from reference/scans/charts/solid_overview.png

# CHART picks which chart supplies the tracing templates, e.g.
#   make place CHART=outline_overview
place: venv
	$(PY) scripts/place_references.py $(if $(CHART),--only $(CHART))

# Place the templates and auto-trace them into outlines in one go. Existing
# drawings are left alone unless you pass OVERWRITE=1.
trace: venv
	$(PY) scripts/place_references.py --trace --set-widths 40 \
	  $(if $(CHART),--only $(CHART)) $(if $(OVERWRITE),--overwrite)

open:
	open -a "/Applications/Glyphs 3.app" $(SOURCE)

build: venv $(SOURCE)
	rm -rf $(FONTS)
	$(PY) -m fontmake -g $(SOURCE) -o ttf otf --output-dir $(FONTS) --verbose WARNING
	@ls -1 $(FONTS)

test: venv
	$(PY) scripts/shape_test.py $(FONT)

# Re-record expectations after an intentional change to the shaping logic.
test-update: venv
	$(PY) scripts/shape_test.py $(FONT) --update

check: venv
	venv/bin/fontbakery check-universal --loglevel WARN $(FONTS)/*.ttf || true

proof: venv
	$(PY) scripts/proof.py $(FONT) -o out/proof.html --family "$(FAMILY)"

all: build test proof

clean:
	rm -rf $(FONTS) out master_ufo instance_ufo variable_ttf

distclean: clean
	rm -rf venv

.PHONY: help venv skeleton inventory dewarp slice sheet adjust measure place trace open build test test-update check proof all clean distclean
