"""Compare inventory vs docx-with-br parsing to find merged heading/body issues."""
from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from extract_inventory import (  # noqa: E402
    DOCX,
    home_chunks_before_first_service,
    section_ranges,
    split_merged_paragraphs,
    text_chunks_from_section,
)


def parse_blocks_with_br(docx: Path) -> list[dict]:
    with zipfile.ZipFile(docx) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")

    rid_to_media: dict[str, str] = {}
    for match in re.finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels_xml):
        rid_to_media[match.group(1)] = match.group(2)

    from extract_inventory import normalize

    blocks: list[dict] = []
    for raw_para in re.split(r"</w:p>", xml):
        raw_para = re.sub(r"<w:br[^/]*/>|<w:cr[^/]*/>", "\n", raw_para)
        plain = normalize(html.unescape(re.sub(r"<[^>]+>", "", raw_para)))
        images = []
        for embed in re.findall(r'r:embed="(rId\d+)"', raw_para):
            target = rid_to_media.get(embed, "")
            if "media/" in target:
                images.append(target.split("/")[-1])
        if plain or images:
            blocks.append({"text": plain, "images": images})
    return blocks


def paragraphs_for_section(blocks: list[dict], key: str, start: int, end: int) -> list[str]:
    section_blocks = blocks[start:end]
    if key == "home":
        chunks = home_chunks_before_first_service(blocks, start, end)
    else:
        chunks = text_chunks_from_section(section_blocks)
    split_chunks = [split_merged_paragraphs(chunk) for chunk in chunks]
    return [p for chunk in split_chunks for p in chunk]


def main() -> int:
    inv = json.loads((ROOT / "content" / "inventory.json").read_text(encoding="utf-8"))
    blocks = parse_blocks_with_br(DOCX)
    ranges = section_ranges(blocks)

    print("MERGED PARAGRAPH AUDIT (docx w:br vs current inventory)\n")
    total_new = 0
    for key, page, start, end in ranges:
        new_paras = paragraphs_for_section(blocks, key, start, end)
        old_paras = inv["sections"][key]["paragraphs"]
        delta = len(new_paras) - len(old_paras)
        if delta:
            total_new += delta
            print(f"{page}: {len(old_paras)} -> {len(new_paras)} (+{delta})")
            old_set = set(old_paras)
            for p in new_paras:
                if p not in old_set and len(p) > 40:
                    print(f"  NEW: {p[:90]}...")
        for p in old_paras:
            if "\n" in p:
                print(f"{page}: inventory still has unsplit newline: {p[:80]}...")
            if len(p) > 120 and p.count(". ") >= 2:
                parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", p, maxsplit=2)
                if len(parts) >= 2 and len(parts[0]) < 90 and len(parts[1]) > 60:
                    print(f"{page}: possible inline merge: H={parts[0][:70]} | B={parts[1][:70]}")

    print(f"\nTotal new paragraphs after w:br fix: {total_new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
