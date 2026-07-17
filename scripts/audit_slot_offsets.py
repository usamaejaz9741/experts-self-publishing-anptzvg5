"""Audit slot manifests for skipped paragraph indices and role misalignment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from page_slots import PAGE_SLOTS  # noqa: E402
from slot_inference import faq_paragraph_index  # noqa: E402


def load_inventory() -> dict:
    return json.loads((ROOT / "content" / "inventory.json").read_text(encoding="utf-8"))


def collect_indices(slots: dict) -> set[int]:
    found: set[int] = set()

    def add(val):
        if isinstance(val, int):
            found.add(val)
        elif isinstance(val, list):
            for x in val:
                add(x)
        elif isinstance(val, dict):
            for x in val.values():
                add(x)

    add(slots)
    return found


def testimonial_range(paragraphs: list[str]) -> tuple[int, int]:
    start = 0
    end = len(paragraphs)
    for i, p in enumerate(paragraphs):
        if p == "What Our Clients Say About Us?":
            start = i
            break
    for i, p in enumerate(paragraphs):
        if p.startswith("Start Your Publishing Journey"):
            end = i
            break
    return start, end


def check_content_rows(page: str, slots: dict) -> list[str]:
    issues = []
    rows = slots.get("content_rows", [])
    nums = [r for r in rows if isinstance(r, int)]
    if nums:
        intro = slots.get("content_intro")
        if isinstance(intro, int) and nums and nums[0] != intro + 1 and "overflow" in rows:
            if intro + 1 not in nums and intro + 1 < max(nums):
                issues.append(f"{page}: content_rows skips index {intro + 1}")
        for a, b in zip(nums, nums[1:]):
            if b - a > 1:
                issues.append(f"{page}: content_rows gap between {a} and {b}")
    return issues


def main() -> int:
    inv = load_inventory()
    issues: list[str] = []
    for info in inv["sections"].values():
        page = info["page"]
        slots = info.get("slots") or PAGE_SLOTS.get(page, {})
        n = len(info["paragraphs"])
        used = collect_indices(slots)
        if slots.get("type") in {"index", "book_marketing", "faq"}:
            continue

        faq_start = faq_paragraph_index(info["paragraphs"])
        testi_start, testi_end = (
            testimonial_range(info["paragraphs"]) if page == "customer-reviews.html" else (n, n)
        )

        for i in range(n):
            if i in used or i >= faq_start:
                continue
            if testi_start <= i < testi_end:
                continue
            p = info["paragraphs"][i]
            if len(p) < 20 or p.startswith("0"):
                continue
            if i > 0 and i < n - 1:
                issues.append(f"{page}: unused paragraph [{i}]: {p[:60]}...")
        issues.extend(check_content_rows(page, slots))
    if issues:
        print("SLOT AUDIT ISSUES:")
        for item in issues:
            print(f"  - {item}")
        return 1
    print("Slot audit: no offset gaps detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
