"""Validate core pages: slot alignment, old UBP phrases, CTA placement."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from apply_content import CORE_PAGES, split_sentences  # noqa: E402
from page_slots import CTA_NO_DOC_PAGES, OLD_PHRASES, PAGE_SLOTS  # noqa: E402

INVENTORY = ROOT / "content" / "inventory.json"
REPORT = ROOT / "content" / "validation-report.md"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def matches(expected: str, actual: str) -> bool:
    if not expected:
        return True
    e, a = norm(expected), norm(actual)
    if not a:
        return False
    n = min(40, len(e))
    return e[:n] in a or a[:n] in e


def paragraphs_for(page: str, inventory: dict) -> list[str]:
    for info in inventory["sections"].values():
        if info["page"] == page:
            return info["paragraphs"]
    return []


def expected_overflow(paragraphs: list[str], intro_idx: int) -> str:
    sents = split_sentences(paragraphs[intro_idx])
    return " ".join(sents[1:]) if len(sents) > 1 else ""


def check_standard_slots(page: str, soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    hero = slots.get("hero", [])
    hero_sels = (
        ".inner-heading .font-35, .about-banner .font-35",
        ".main-heading, .bann-heading h1",
        ".inner-heading > p, .inner-heading p.reveal, .about-banner p.reveal",
    )
    for sel, idx in zip(hero_sels, hero):
        el = soup.select_one(sel)
        if el and not matches(paragraphs[idx], el.get_text()):
            failures.append(f"{page} hero[{idx}]: expected {preview(paragraphs[idx])}")

    if not slots.get("cta_no_doc") and (cta := slots.get("cta")):
        cta_el = soup.select_one("section.cta-sec .cta-content")
        if cta_el:
            texts = [
                norm(cta_el.select_one("h3.bg-rect").get_text()) if cta_el.select_one("h3.bg-rect") else "",
                norm(cta_el.select_one("h2.sec-hd").get_text()) if cta_el.select_one("h2.sec-hd") else "",
                norm(cta_el.select_one("p").get_text()) if cta_el.select_one("p") else "",
            ]
            start = 1 if slots.get("cta_h3_fixed") else 0
            for j, idx in enumerate(cta):
                sel_i = start + j
                if sel_i < len(texts) and not matches(paragraphs[idx], texts[sel_i]):
                    failures.append(
                        f"{page} CTA slot {sel_i}: expected {preview(paragraphs[idx])} got {preview(texts[sel_i])}"
                    )
                about = soup.select_one("section.about-1")
                if about and paragraphs[idx][:30] in norm(about.get_text()):
                    failures.append(f"{page} CTA line {idx} appears in about-1 instead of cta-sec")

    if slots.get("cta_no_doc") and page in CTA_NO_DOC_PAGES:
        warnings.append(f"{page}: CTA has no doc source (known gap)")

    content_rows = slots.get("content_rows", [])
    content_els = soup.select("section.about-1 .content p.para-color")
    intro_idx = slots.get("content_intro")
    for i, spec in enumerate(content_rows):
        if i >= len(content_els):
            break
        expected = expected_overflow(paragraphs, intro_idx) if spec == "overflow" else paragraphs[spec]
        if expected and not matches(expected, content_els[i].get_text()):
            failures.append(f"{page} content_rows[{i}]: mismatch")

    make = soup.select_one("section.make-unique .make-content")
    if make and "make_title" in slots:
        h2 = make.select_one("h2")
        if h2 and not matches(paragraphs[slots["make_title"]], h2.get_text()):
            failures.append(f"{page} make_title: mismatch")

    return failures, warnings


def check_about(page: str, soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    cta = soup.select_one("section.cta-sec .cta-content")
    if cta:
        for sel, idx in zip(("h3.bg-rect", "h2.sec-hd", "p"), slots["cta"]):
            el = cta.select_one(sel)
            if el and not matches(paragraphs[idx], el.get_text()):
                failures.append(
                    f"{page} CTA {sel}: expected {preview(paragraphs[idx])} got {preview(el.get_text())}"
                )
    banner = soup.select_one(".about-banner .main-heading")
    if banner and not matches(paragraphs[slots["banner"][0]], banner.get_text()):
        failures.append(f"{page} banner title mismatch")
    return failures, warnings


def check_book_publishing(page: str, soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    cta = soup.select_one("section.cta-sec .cta-content")
    if cta:
        if not matches(slots["cta_h3_fixed"], cta.select_one("h3.bg-rect").get_text()):
            failures.append(f"{page} CTA h3 fixed label mismatch")
        for sel, idx in zip(("h2.sec-hd", "p"), slots["cta"]):
            if not matches(paragraphs[idx], cta.select_one(sel).get_text()):
                failures.append(f"{page} CTA {sel} mismatch")
    kdp_h2 = soup.select_one("section.kdp-sec h2.sec-hd")
    if kdp_h2 and "Amazon KDP" in kdp_h2.get_text():
        failures.append(f"{page} KDP still has Amazon KDP heading")
    return failures, warnings


def preview(text: str, n: int = 55) -> str:
    t = norm(text)
    return t if len(t) <= n else t[: n - 3] + "..."


def check_old_phrases(page: str, html: str) -> list[str]:
    failures: list[str] = []
    for phrase in OLD_PHRASES:
        if phrase == "Struggling With Amazon KDP?" and page == "book-publishing.html":
            if phrase in html and "package" not in html.lower():
                pass
            continue
        if phrase in html:
            if phrase in {"Reach from Simple Draft to Published Success", "Let Your Words Find Their Readers"} and page in CTA_NO_DOC_PAGES:
                continue
            failures.append(f"{page}: old phrase {phrase!r}")
    return failures


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    all_failures: list[str] = []
    all_warnings: list[str] = []

    for page in CORE_PAGES:
        path = ROOT / page
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = paragraphs_for(page, inventory)
        slots = PAGE_SLOTS.get(page, {})

        if slots.get("type") == "book_publishing":
            f, w = check_book_publishing(page, soup, paragraphs, slots)
        elif page == "about-us.html":
            f, w = check_about(page, soup, paragraphs, slots)
        elif slots and not slots.get("type"):
            f, w = check_standard_slots(page, soup, paragraphs, slots)
        else:
            f, w = [], []
            if page == "pricing.html":
                w.append(f"{page}: CTA has no doc source (known gap)")

        all_failures.extend(f)
        all_warnings.extend(w)
        all_failures.extend(check_old_phrases(page, html))

    lines = ["# Content Validation Report", "", f"Pages checked: {len(CORE_PAGES)}", ""]
    if all_failures:
        lines.append("## Failures")
        for item in all_failures:
            lines.append(f"- {item}")
        lines.append("")
    if all_warnings:
        lines.append("## Warnings")
        for item in all_warnings:
            lines.append(f"- {item}")
        lines.append("")
    if not all_failures and not all_warnings:
        lines.append("All checks passed.")
    elif not all_failures:
        lines.append("No hard failures (warnings only).")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if all_failures:
        print("VALIDATION FAILED:")
        for item in all_failures:
            print(f"  - {item}")
    else:
        print("Validation passed.")
    for item in all_warnings:
        print(f"  WARN: {item}")
    print(f"Report: {REPORT}")
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
