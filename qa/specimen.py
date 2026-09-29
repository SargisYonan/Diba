"""Renders text proofs of the built font to PNG, for the README.

    python qa/specimen.py        writes documentation/proof-*.png

Text is shaped by HarfBuzz and drawn from the font's own outlines, so the
images look the same on every machine and need no system fonts or tools.
"""

import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, Font, shape  # noqa: E402
from proof import ALPHABET, PRAYER, WORDS  # noqa: E402

DOCS = os.path.join(ROOT, "documentation")
WIDTH = 1600          # final image width in pixels
MARGIN = 72
SS = 3                # supersampling factor for smooth edges
PAPER = (251, 250, 247)
INK = (29, 27, 24)
MUTED = (120, 114, 104)
RULE = (228, 224, 216)


class Page:
    """Lays out right-to-left lines of text and Latin captions, top to bottom."""

    def __init__(self, font):
        self.font = font
        self.items = []   # ("text", runs...) or ("label", ...)
        self.y = MARGIN

    def label(self, text, size=22, color=MUTED, gap=14):
        self.items.append(("label", text, size, color, self.y))
        self.y += size + gap

    def rule(self, gap=36):
        self.y += gap / 2
        self.items.append(("rule", self.y))
        self.y += gap / 2

    def words(self, text, size, leading=1.9, align="right"):
        """Wrap `text` to the page width and set it at `size` pixels per em."""
        scale = size / 1000
        room = (WIDTH - 2 * MARGIN) / scale
        lines, line = [], []
        for word in text.split():
            trial = " ".join(line + [word])
            if line and width(self.font, shape(self.font.path, trial)) > room:
                lines.append(" ".join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(" ".join(line))
        for text_line in lines:
            run = shape(self.font.path, text_line)
            self.y += size * 1.05
            w = width(self.font, run) * scale
            x = WIDTH - MARGIN - w if align == "right" else MARGIN
            self.items.append(("text", run, scale, x, self.y))
            self.y += size * (leading - 1.05)

    def render(self, path):
        height = int(self.y + MARGIN)
        mask = Image.new("1", (WIDTH * SS, height * SS), 0)
        for item in self.items:
            if item[0] == "text":
                _, run, scale, x, baseline = item
                draw_run(mask, self.font, run, scale, x, baseline)
        ink = mask.convert("L").resize((WIDTH, height), Image.Resampling.LANCZOS)
        img = Image.composite(Image.new("RGB", (WIDTH, height), INK),
                              Image.new("RGB", (WIDTH, height), PAPER), ink)
        draw = ImageDraw.Draw(img)
        for item in self.items:
            if item[0] == "label":
                _, text, size, color, y = item
                draw.text((MARGIN, y), text, fill=color, font=ImageFont.load_default(size=size))
            elif item[0] == "rule":
                draw.line((MARGIN, item[1], WIDTH - MARGIN, item[1]), fill=RULE, width=2)
        img.save(path, optimize=True)
        print(f"wrote {os.path.relpath(path, ROOT)} ({WIDTH}x{height})")


def width(font, run):
    """Width of a shaped line in font units: the last glyph's pen position
    plus its advance."""
    name, x, _ = run[-1]
    return x + font.glyph(name).width


def draw_run(mask, font, run, scale, x0, baseline):
    """Fill each glyph's outlines into `mask`. Contours are XORed so counters
    come out as holes; glyphs are ORed so joints merge."""
    for name, gx, gy in run:
        glyph = font.glyph(name)
        if not glyph.polys:
            continue
        pts = [[((x0 + (gx + px) * scale) * SS, (baseline - (gy + py) * scale) * SS)
                for px, py in poly] for poly in glyph.polys]
        xs = [p[0] for poly in pts for p in poly]
        ys = [p[1] for poly in pts for p in poly]
        left, top = int(min(xs)) - 1, int(min(ys)) - 1
        right, bottom = int(max(xs)) + 2, int(max(ys)) + 2
        box = (left, top, right, bottom)
        shape_mask = Image.new("1", (right - left, bottom - top), 0)
        for poly in pts:
            layer = Image.new("1", shape_mask.size, 0)
            ImageDraw.Draw(layer).polygon([(x - left, y - top) for x, y in poly], fill=1)
            shape_mask = ImageChops.logical_xor(shape_mask, layer)
        mask.paste(ImageChops.logical_or(mask.crop(box), shape_mask), box)



def main():
    font = Font()
    os.makedirs(DOCS, exist_ok=True)

    # Text: the alphabet, words and a paragraph at reading sizes.
    page = Page(font)
    page.label("Diba", size=44, color=INK, gap=10)
    page.label("East Syriac typeface  ·  text proof", size=22)
    page.rule()
    page.words(ALPHABET, 120, leading=1.6)
    page.words(" ".join(ALPHABET), 64, leading=1.7)
    page.rule()
    page.label("Words", size=20)
    page.words(" ".join(WORDS), 60, leading=1.75)
    page.rule()
    page.label("The Lord's Prayer", size=20)
    page.words(PRAYER, 44, leading=1.8)
    page.rule()
    for size in (32, 24, 18):
        page.label(f"{size} px", size=16, gap=0)
        page.words(PRAYER, size, leading=1.7)
    page.render(os.path.join(DOCS, "proof-text.png"))

    # Joins: every dual-joining letter between Beths, then tripled.
    page = Page(font)
    page.label("Diba  ·  joining proof", size=30, color=INK, gap=10)
    page.label("Each dual-joining letter between two Beths, then three in a row", size=20)
    page.rule()
    dual = "ܒܓܚܛܝܟܠܡܢܣܤܥܦܩܫ"
    page.words(" ".join("ܒ" + c + "ܒ" for c in dual), 84, leading=1.9)
    page.rule()
    page.words(" ".join(c * 3 for c in dual), 84, leading=1.9)
    page.rule()
    page.label("Right-joining letters after Beth", size=20)
    page.words(" ".join("ܒ" + c for c in "ܐܕܗܘܙܨܪܬ"), 84, leading=1.9)
    page.render(os.path.join(DOCS, "proof-joins.png"))


if __name__ == "__main__":
    main()
