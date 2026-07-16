"""Print expected inventory text for each PAGE_SLOTS entry (manifest sanity check)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from page_slots import PAGE_SLOTS  # noqa: E402


def load_inventory() -> dict:
    return json.loads((ROOT / "content" / "inventory.json").read_text(encoding="utf-8"))


def paragraphs_for(page: str, inventory: dict) -> list[str]:
    for info in inventory["sections"].values():
        if info["page"] == page:
            return info["paragraphs"]
    return []


def preview(text: str, n: int = 70) -> str:
    t = " ".join(text.split())
    return t if len(t) <= n else t[: n - 3] + "..."


def show_idx(paragraphs: list[str], idx: int | str) -> str:
    if idx == "overflow":
        return "<overflow from content_intro>"
    if not isinstance(idx, int) or idx < 0 or idx >= len(paragraphs):
        return f"<MISSING idx {idx}>"
    return preview(paragraphs[idx])


def main() -> None:
    inventory = load_inventory()
    for page, slots in PAGE_SLOTS.items():
        paragraphs = paragraphs_for(page, inventory)
        print(f"\n{'=' * 72}\n{page} ({len(paragraphs)} paragraphs)")
        if not paragraphs:
            print("  WARNING: no inventory section")
            continue
        if slots.get("type") == "book_publishing":
            for key in ("banner", "s1_body", "cta", "testi"):
                if key in slots:
                    print(f"  {key}: {[show_idx(paragraphs, i) for i in (slots[key] if isinstance(slots[key], list) else [slots[key]])]}")
            continue
        if slots.get("type") in {"index", "pricing", "faq", "book_marketing"}:
            print(f"  type={slots.get('type')} (custom handler)")
            continue
        for key in ("hero", "content_heading", "content_heading_split", "content_intro", "content_rows", "cta", "make_title", "make_body", "banner", "about_rows"):
            if key not in slots:
                continue
            val = slots[key]
            if key == "content_heading_split":
                a, b = val
                print(f"  {key}: [{show_idx(paragraphs, a)}] | [{show_idx(paragraphs, b)}]")
            elif isinstance(val, list):
                print(f"  {key}: {[show_idx(paragraphs, i) for i in val]}")
            else:
                print(f"  {key}: {show_idx(paragraphs, val)}")
        if slots.get("cta_no_doc"):
            print("  cta_no_doc: True")


if __name__ == "__main__":
    main()
