"""Give an unhinted TrueType font smart dropout control, as `gftools
fix-nonhinting` does: a short `prep` program and a `gasp` table.

ttfautohint cannot hint Syriac (it has no Syriac script module), so the font
ships unhinted. Without dropout control, thin strokes can vanish when Windows
rasterises at small sizes; these two tables turn it on.

    python scripts/fix_hinting.py fonts/Diba-Regular.ttf
"""

import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram


def main(path):
    font = TTFont(path)
    prep = newTable("prep")
    prep.program = ttProgram.Program()
    prep.program.fromAssembly(["PUSHW[ ]", "511", "SCANCTRL[ ]", "PUSHB[ ]", "4", "SCANTYPE[ ]"])
    font["prep"] = prep
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}   # grid-fit and smooth at every size
    font["gasp"] = gasp
    font.save(path)


if __name__ == "__main__":
    main(sys.argv[1])
