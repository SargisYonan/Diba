SOURCE := sources/Diba.glyphs
FONT   := fonts/Diba-Regular.ttf
VENV   := venv
PY     := $(VENV)/bin/python

.DEFAULT_GOAL := help

help:
	@echo "Diba"
	@echo "  make build       compile $(FONT) from $(SOURCE)"
	@echo "  make qa          report problems with the letters, joins and marks"
	@echo "  make test        pass/fail tests for joins, marks and coverage"
	@echo "  make fontbakery  run fontbakery's universal checks (report in out/)"
	@echo "  make proof       write out/proof.html and open it"
	@echo "  make images      render the README images into documentation/"
	@echo "  make all         build, qa, proof, images, then test"
	@echo "  make ci          what GitHub runs on every push: fails on any QA error,"
	@echo "                   failing test or fontbakery failure"
	@echo "  make clean       remove out/ and the built font"
	@echo ""
	@echo "To check a font exported from Glyphs instead of building one:"
	@echo "  make qa proof FONT=path/to/Diba-Regular.ttf"

$(VENV)/.done: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -r requirements.txt
	touch $@

venv: $(VENV)/.done

$(FONT): $(SOURCE) $(VENV)/.done
	@mkdir -p fonts
	$(VENV)/bin/fontmake -g $(SOURCE) -o ttf --overlaps-backend pathops \
		--output-path $(FONT) 2>&1 | grep -v "^INFO" || true
	@test -f $(FONT)
	$(PY) scripts/fix_hinting.py $(FONT)

build: $(FONT)

# Use the font given on the command line as is; otherwise build it first.
FONT_DEP := $(if $(filter command line,$(origin FONT)),,$(FONT))

qa: $(FONT_DEP) $(VENV)/.done
	FONT=$(FONT) $(PY) qa/check.py

test: $(FONT_DEP) $(VENV)/.done
	FONT=$(FONT) $(PY) -m pytest tests -q

fontbakery: $(FONT_DEP) $(VENV)/.done
	@mkdir -p out
	$(VENV)/bin/fontbakery check-universal $(FONT) --succinct -C \
		--html out/fontbakery.html --ghmarkdown out/fontbakery.md

proof: $(FONT_DEP) $(VENV)/.done
	FONT=$(FONT) $(PY) qa/check.py --quiet
	FONT=$(FONT) $(PY) qa/proof.py
	@[ -n "$$CI" ] || open out/proof.html 2>/dev/null || true

IMAGES := $(addprefix documentation/,word-1.svg word-2.svg word-3.svg word-4.svg word-5.svg \
	alphabet.svg proof-charset.svg proof-forms.svg proof-joins.svg proof-vowels.svg)

# One run writes all the images.
documentation/word-1.svg: $(FONT) qa/specimen.py qa/proof.py $(VENV)/.done
	FONT=$(FONT) $(PY) qa/specimen.py
$(filter-out documentation/word-1.svg,$(IMAGES)): documentation/word-1.svg

images: $(IMAGES)

all: build qa proof images test

# Always rebuild from the source, so CI tests the source rather than a stale
# committed font.
ci: $(VENV)/.done
	rm -f $(FONT)
	$(MAKE) build
	FONT=$(FONT) $(PY) qa/check.py --strict
	FONT=$(FONT) $(PY) -m pytest tests -q
	$(MAKE) fontbakery proof images

clean:
	rm -rf out $(FONT) master_ufo instance_ufo .pytest_cache

.PHONY: help venv build qa test fontbakery proof images all ci clean
