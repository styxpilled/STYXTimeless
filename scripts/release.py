"""Packs fonts/ into release zips in release/ (run after build.py).

    python scripts/release.py

Variable: the variable TTFs. Static: OTF and hinted TTF, 100-900. Web: WOFF2 only,
variable and static, full and in subsets, with CSS. Each zip has both families
and OFL.txt.
"""

import shutil
import zipfile
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
OUT = ROOT / "release"
FAMILIES = ("STYXTimeless", "STYXTimelessRound")
ZIPS = {  # zip name: {path in the family folder of the zip: (path in fonts/<family>, glob)}
    "Variable": {"": ("variable", "*.ttf")},
    "Static": {"otf": ("otf", "*.otf"), "ttf": ("ttf", "*.ttf")},
    "Web": {"variable": ("variable", "*.woff2"), "static": ("woff2", "*.woff2"), "subset": ("subset", "**/*")},
}


def version():
    return f"{TTFont(FONTS / 'STYXTimeless' / 'variable' / 'STYXTimeless[ital,wght].ttf')['head'].fontRevision:.3f}"


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    v = version()
    for kind, parts in ZIPS.items():
        top = f"STYXTimeless-{v}-{kind}"
        path = OUT / f"{top}.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(ROOT / "OFL.txt", f"{top}/OFL.txt")
            for family in FAMILIES:
                for dest, (src, pattern) in parts.items():
                    base = FONTS / family / src
                    for f in sorted(base.glob(pattern)):
                        if f.is_file():
                            z.write(f, "/".join(p for p in (top, family, dest, f.relative_to(base).as_posix()) if p))
        print(path.name, f"{path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
