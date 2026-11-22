"""Builds STYX Timeless and STYX Timeless Round into fonts/.

Each family: variable font (TTF, WOFF2), statics 100-900 (TTF hinted, OTF,
WOFF2), and the WOFF2 fonts in three web subsets with CSS files.

    pip install -r requirements.txt
    python scripts/build.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.subset import Options, Subsetter, parse_unicodes
from fontTools.ttLib import TTFont
from ttfautohint import ttfautohint

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = [
    ("STYXTimeless", "STYX Timeless", "sources/STYXTimeless.designspace"),
    ("STYXTimelessRound", "STYX Timeless Round", "sources/Round/STYXTimelessRound.designspace"),
]
# Google Fonts ranges; latin also takes the symbols that all scripts use
# (combining marks, Greek math letters, figures, fractions, arrows, math, ligatures)
SUBSETS = {
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02D8-02DD,U+0300-036F,"
             "U+0394,U+03A9,U+03BC,U+03C0,U+2000-206F,U+2070-209F,U+20AC,U+2122,U+2150-218F,"
             "U+2190-21FF,U+2200-22FF,U+25CA,U+FB00-FB06,U+FEFF,U+FFFD",
    "latin-ext": "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,"
                 "U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,"
                 "U+2113,U+2C60-2C7F,U+A720-A7FF",
    "cyrillic": "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116",
}


def fontmake(*args):
    subprocess.run([sys.executable, "-m", "fontmake", *args], check=True, capture_output=True, cwd=ROOT)


def woff2(src, dest):
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob("*.ttf")):
        font = TTFont(f)
        font.flavor = "woff2"
        font.save(dest / f"{f.stem}.woff2")


def subset(out, name, unicodes):
    options = Options(layout_features=["*"], name_IDs=["*"], name_languages=["*"], flavor="woff2")
    for kind, src in (("variable", "variable"), ("static", "ttf")):
        dest = out / "subset" / name / kind
        dest.mkdir(parents=True)
        for f in sorted((out / src).glob("*.ttf")):
            font = TTFont(f)
            s = Subsetter(options)
            s.populate(unicodes=parse_unicodes(unicodes.replace(",", " ")))
            s.subset(font)
            font.flavor = "woff2"
            font.save(dest / f"{f.stem}.woff2")


def face(family, style, weight, url, name):
    return f"""/* {name} */
@font-face {{
  font-family: "{family}";
  font-style: {style};
  font-weight: {weight};
  font-display: swap;
  src: url("{url}") format("woff2");
  unicode-range: {SUBSETS[name].replace(",", ", ")};
}}
"""


def css(out, file, family):
    order = ("latin-ext", "cyrillic", "latin")
    variable = [face(family, style, "100 900", f"{name}/variable/{file}[ital,wght].woff2", name)
                for name in order for style in ("normal", "italic")]
    (out / "subset" / f"{file}-variable.css").write_text("".join(variable))
    static = []
    for f in sorted((out / "ttf").glob("*.ttf"), key=lambda f: (TTFont(f)["OS/2"].usWeightClass, f.stem)):
        os2 = TTFont(f)["OS/2"]
        style = "italic" if os2.fsSelection & 1 else "normal"
        static += [face(family, style, os2.usWeightClass, f"{name}/static/{f.stem}.woff2", name) for name in order]
    (out / "subset" / f"{file}-static.css").write_text("".join(static))


def build(file, family, designspace):
    out = ROOT / "fonts" / file
    shutil.rmtree(out, ignore_errors=True)
    print(f"{family}: variable")
    fontmake("-m", designspace, "-o", "variable", "--output-path", str(out / "variable" / f"{file}[ital,wght].ttf"))
    woff2(out / "variable", out / "variable")
    print(f"{family}: statics")
    for kind in ("ttf", "otf"):
        fontmake("-m", designspace, "-i", "-o", kind, "--output-dir", str(out / kind))
    for f in sorted((out / "ttf").glob("*.ttf")):
        hinted = f.with_suffix(".hinted")
        ttfautohint(in_file=str(f), out_file=str(hinted), no_info=True)
        hinted.replace(f)
    woff2(out / "ttf", out / "woff2")
    print(f"{family}: subsets")
    for name, unicodes in SUBSETS.items():
        subset(out, name, unicodes)
    css(out, file, family)


if __name__ == "__main__":
    for args in FAMILIES:
        build(*args)
    print("Done: fonts/")
