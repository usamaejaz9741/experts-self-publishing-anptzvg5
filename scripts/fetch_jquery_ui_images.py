"""Download jQuery UI 1.11.4 theme PNGs referenced by assets/css/jquery-ui.css."""
from __future__ import annotations

import io
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "assets" / "css" / "jquery-ui.css"
OUT = ROOT / "assets" / "css" / "images"
ZIP_URL = "https://jqueryui.com/resources/download/jquery-ui-1.11.4.zip"

# Fallback sprite/texture sources from the stock smoothness theme.
ICON_FALLBACK = "ui-icons_222222_256x240.png"
BG_FALLBACKS = [
    ("gloss-wave", "ui-bg_gloss-wave_35_f6a828_500x100.png"),
    ("inset-hard", "ui-bg_highlight-soft_100_eeeeee_1x100.png"),
    ("glass", "ui-bg_glass_65_ffffff_1x400.png"),
    ("flat", "ui-bg_flat_10_000000_40x100.png"),
]


def main() -> None:
    css = CSS.read_text(encoding="utf-8")
    names = sorted(set(re.findall(r"images/([^\"')]+?)\.png", css)))
    print(f"CSS references {len(names)} image(s)")

    with urllib.request.urlopen(ZIP_URL, timeout=60) as resp:
        data = resp.read()

    OUT.mkdir(parents=True, exist_ok=True)
    copied = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zip_files = {Path(n).name: n for n in zf.namelist() if n.endswith(".png")}

        def read_zip(filename: str) -> bytes:
            path = zip_files.get(filename)
            if not path:
                raise KeyError(filename)
            return zf.read(path)

        for name in names:
            dest = OUT / f"{name}.png"
            if name in zip_files:
                dest.write_bytes(read_zip(name))
                copied += 1
                continue

            if name.startswith("ui-icons_"):
                dest.write_bytes(read_zip(ICON_FALLBACK))
                copied += 1
                continue

            if name.startswith("ui-bg_"):
                fallback = None
                for key, candidate in BG_FALLBACKS:
                    if key in name:
                        fallback = candidate
                        break
                if fallback and fallback in zip_files:
                    dest.write_bytes(read_zip(fallback))
                    copied += 1
                else:
                    print(f"no fallback for {name}.png")
                continue

    print(f"Wrote {copied} image(s) to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
