"""Renders specimen/index.html to PNG images with a Chromium browser (run after build.py).

    python scripts/specimen.py [--browser PATH] [--out DIR] [NAME=QUERY ...]

Without NAME=QUERY it writes the default images. QUERY sets the page: title=...,
show= sections joined by + (main, compare), theme=...
"""

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "specimen" / "index.html").as_uri()
WIDTH = 1600
IMAGES = {
    "STYXTimeless": "title=STYX%20Timeless&show=main%2Bcompare&theme=bauhaus",
}


def run(browser, *args):
    with tempfile.TemporaryDirectory() as profile:
        return subprocess.run([browser, "--headless", "--disable-gpu", "--hide-scrollbars", "--disable-lcd-text",
                               f"--user-data-dir={profile}", "--virtual-time-budget=5000", *args],
                              check=True, capture_output=True, text=True, encoding="utf-8").stdout


def render(browser, query, png):
    url = f"{PAGE}?{query}"
    dom = run(browser, f"--window-size={WIDTH},1000", "--dump-dom", url)
    height = int(re.search(r'data-height="(\d+)"', dom).group(1))
    run(browser, f"--window-size={WIDTH},{height}", "--force-device-scale-factor=2", f"--screenshot={png}", url)
    print(png, f"{WIDTH * 2} x {height * 2}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", default="chrome")
    ap.add_argument("--out", type=Path, default=ROOT / "specimen")
    ap.add_argument("images", nargs="*", help="NAME=QUERY")
    a = ap.parse_args()
    images = dict(i.split("=", 1) for i in a.images) or IMAGES
    a.out.mkdir(parents=True, exist_ok=True)
    for name, query in images.items():
        render(a.browser, query, a.out / f"{name}.png")


if __name__ == "__main__":
    main()
