"""Per-page inventory paragraph index maps for HTML slot alignment.

Auto-generated from image-boundary extraction. Run ``scripts/extract_inventory.py``
to refresh ``content/page-slots.json``, then this module reloads it.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SLOTS_FILE = ROOT / "content" / "page-slots.json"

_FALLBACK: dict[str, dict] = {}


def _load_page_slots() -> dict[str, dict]:
    if _SLOTS_FILE.exists():
        return json.loads(_SLOTS_FILE.read_text(encoding="utf-8"))
    return _FALLBACK


PAGE_SLOTS: dict[str, dict] = _load_page_slots()

OLD_PHRASES = [
    "Reach from Simple Draft to Published Success",
    "Let Your Words Find Their Readers",
    "Let Your Words Reach the World",
    "Connect with us today and turn uncertainty",
    "Talk with our experts and get the guidance you need to convert your raw manuscript",
    "United Book Publishing",
    "Struggling With Amazon KDP?",
]

CTA_NO_DOC_PAGES = {page for page, slots in PAGE_SLOTS.items() if slots.get("cta_no_doc")}
