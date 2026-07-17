"""Find headings in HTML that contain long body-like copy (merged heading/body issues)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("*.html"))
MIN_LEN = 120


def main() -> int:
    issues: list[str] = []
    for path in PAGES:
        if path.name.startswith("cigar-") or path.name.startswith("ralph-"):
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for sel in ("h1", "h2", "h3", ".sec-hd", ".font-35", ".main-heading"):
            for el in soup.select(sel):
                text = re.sub(r"\s+", " ", el.get_text()).strip()
                if len(text) < MIN_LEN:
                    continue
                if text.count(". ") >= 2 or len(text) > 180:
                    issues.append(f"{path.name} {sel}: {text[:100]}...")

    if issues:
        print("HEADING/BODY MERGE ISSUES IN HTML:")
        for item in issues:
            print(f"  - {item}")
        return 1
    print("No long heading merges detected in HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
