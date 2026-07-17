"""Audit HTML pages for common slot-mapping issues."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    "index.html",
    "author-website.html",
    "pr-and-publicity.html",
    "book-editing-proofreading.html",
    "book-cover-design.html",
    "ghostwriting.html",
    "book-illustration.html",
    "book-video-trailers.html",
    "creative-writing.html",
    "children-book-illustration.html",
    "screenplay-script-writing.html",
    "book-publishing.html",
    "book-marketing.html",
    "pricing.html",
    "about-us.html",
    "published-books.html",
    "customer-reviews.html",
    "faq.html",
]

PREFIX_PAGES = {"ghostwriting.html", "book-video-trailers.html"}


def main() -> int:
    issues: list[str] = []
    for page in PAGES:
        path = ROOT / page
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")

        for h1 in soup.select(
            ".inner-banner .main-heading, .about-banner .main-heading, .bann-heading h1"
        ):
            if not h1.get_text(strip=True):
                issues.append(f"{page}: empty hero h1")

        if page in PREFIX_PAGES:
            prefix_el = soup.select_one(".inner-banner .font-35, .inner-heading .font-35")
            h1 = soup.select_one(".inner-banner .main-heading, .inner-heading .main-heading")
            if prefix_el and h1 and not h1.get_text(strip=True):
                issues.append(f"{page}: hero prefix set but h1 empty")

        box = soup.select_one("section.about-1 .content-box")
        if box:
            f35 = (box.select_one(".font-35") or {}).get_text(strip=True) if box.select_one(".font-35") else ""
            h2 = (box.select_one("h2") or {}).get_text(strip=True) if box.select_one("h2") else ""
            intro_el = box.select_one("p.para-color")
            intro = intro_el.get_text(strip=True) if intro_el else ""
            if not f35 and not h2 and intro and not intro.endswith("."):
                issues.append(f"{page}: about heading missing (title in intro): {intro[:50]}...")
            if f35 and not h2 and intro and len(intro) < 90 and not intro.endswith("."):
                issues.append(f"{page}: split heading may be wrong (only f35 + short intro)")

        for h3 in soup.select(".why-choose-sec .choose-box h3"):
            t = h3.get_text(strip=True)
            if re.match(r"^0?\d+\.", t) or t == "Get Started":
                issues.append(f"{page}: process step in why-choose box: {t}")

        for li in soup.select(".process-step li"):
            h4 = li.select_one("h4")
            if h4 and not h4.get_text(strip=True):
                issues.append(f"{page}: empty process-step title")

    if issues:
        print("PAGE CONTENT AUDIT ISSUES:")
        for item in issues:
            print(f"  - {item}")
        return 1
    print("Page content audit: no issues detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
