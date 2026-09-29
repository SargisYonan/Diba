SOURCE := sources/Diba.glyphs
FONT   := fonts/Diba-Regular.ttf
VENV   := venv
PY     := $(VENV)/bin/python

.DEFAULT_GOAL := help

help:
	@echo "Diba"
	@echo "  make build   compile $(FONT) from $(SOURCE)"
	@echo "  make qa      report problems with the letters and joins"
	@echo "  make test    pass/fail tests for joining (fails on broken joins)"
	@echo "  make proof   write out/proof.html and open it"
	@echo "  make images  render the text proofs in documentation/ (linked from the README)"
	@echo "  make all     build, qa, proof, images, then test"
	@echo "  make clean   remove out/ and the built font"
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

build: $(FONT)

qa: $(if $(filter command line,$(origin FONT)),,$(FONT)) $(VENV)/.done
	FONT=$(FONT) $(PY) qa/check.py

test: $(if $(filter command line,$(origin FONT)),,$(FONT)) $(VENV)/.done
	FONT=$(FONT) $(PY) -m pytest tests -q

proof: $(if $(filter command line,$(origin FONT)),,$(FONT)) $(VENV)/.done
	FONT=$(FONT) $(PY) qa/check.py --quiet
	FONT=$(FONT) $(PY) qa/proof.py
	@open out/proof.html 2>/dev/null || true

IMAGES := documentation/proof-text.png documentation/proof-joins.png

# One run writes both images.
documentation/proof-text.png: $(FONT) qa/specimen.py qa/proof.py $(VENV)/.done
	FONT=$(FONT) $(PY) qa/specimen.py
documentation/proof-joins.png: documentation/proof-text.png

images: $(IMAGES)

all: build qa proof images test

clean:
	rm -rf out $(FONT) master_ufo instance_ufo .pytest_cache

.PHONY: help venv build qa test proof images all clean
