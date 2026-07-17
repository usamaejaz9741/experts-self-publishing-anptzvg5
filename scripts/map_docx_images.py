"""Map docx images to page sections and export a placement report."""
from __future__ import annotations

import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "Experts Self Publishing Content (New).docx"
OUT_DIR = ROOT / "content" / "docx-images"
REPORT = ROOT / "content" / "image-placement-map.json"

# New doc section headers -> html page
SECTION_HEADERS = [
    (r"^Home Page$", "index.html", "home"),
    (r"^Services \( Athor\)$", "author-website.html", "author-website"),
    (r"^PR & Publicity services$", "pr-and-publicity.html", "pr-publicity"),
    (r"^Book editing proofreading$", "book-editing-proofreading.html", "editing"),
    (r"^Book Cover Design Services$", "book-cover-design.html", "cover-design"),
    (r"^Ghostwriting$", "ghostwriting.html", "ghostwriting"),
    (r"^Book Illustration$", "book-illustration.html", "illustration"),
    (r"^Book Video Trailer$", "book-video-trailers.html", "video-trailer"),
    (r"^Creative Writing$", "creative-writing.html", "creative-writing"),
    (r"^Children.s Book$", "children-book-illustration.html", "children-illustration"),
    (r"^Screenplat Script Writing$", "screenplay-script-writing.html", "screenplay"),
    (r"^Book Publishing$", "book-publishing.html", "book-publishing"),
    (r"^Book Marketing$", "book-marketing.html", "book-marketing"),
    (r"^Pricing$", "pricing.html", "pricing"),
    (r"^About Experts Self\s+Publishing$", "about-us.html", "about"),
    (r"^RESOURCES\(PUBLIC BOOKS\)$", "published-books.html", "published-books"),
    (r"^RESOURCES\(CUSTOMER REVIEWS\)$", "customer-reviews.html", "customer-reviews"),
    (r"^FAQ$", "faq.html", "faq"),
]


def normalize(text: str) -> str:
    return (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\ufffd", "'")
        .strip()
    )


def parse_document(docx: Path):
    with zipfile.ZipFile(docx) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")

    rid_to_media: dict[str, str] = {}
    for match in re.finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels_xml):
        rid_to_media[match.group(1)] = match.group(2)

    blocks: list[dict] = []
    for raw_para in re.split(r"</w:p>", xml):
        plain = normalize(re.sub(r"<[^>]+>", "", raw_para))
        images = []
        for embed in re.findall(r'r:embed="(rId\d+)"', raw_para):
            target = rid_to_media.get(embed, "")
            if "media/" in target:
                images.append(target.split("/")[-1])
        if plain or images:
            blocks.append({"text": plain, "images": images})

    return blocks, rid_to_media


def match_section(text: str) -> tuple[str, str, str] | None:
    for pattern, html_page, key in SECTION_HEADERS:
        if re.match(pattern, text, re.I):
            return html_page, key, text
    return None


def slot_guess(section_key: str, index_in_section: int, total_images: int) -> str:
    """Heuristic HTML slot based on typical page layout order."""
    service_order = [
        "hero",
        "content_intro",
        "cta",
        "make_section",
        "benefits_grid",
        "faq",
        "footer_cta",
    ]
    if section_key == "home":
        home_order = [
            "hero",
            "partner_section",
            "services_grid",
            "process_steps",
            "testimonials",
            "more_than_publisher",
            "journey_cta",
        ]
        return home_order[min(index_in_section, len(home_order) - 1)]
    if section_key == "book-publishing":
        pub_order = ["hero", "why_choose", "cta", "kdp_section", "packages", "faq", "banner"]
        return pub_order[min(index_in_section, len(pub_order) - 1)]
    if section_key == "book-marketing":
        mkt_order = ["hero", "intro", "cta", "why_section", "services", "process", "faq"]
        return mkt_order[min(index_in_section, len(mkt_order) - 1)]
    if section_key in ("pricing", "about", "published-books", "customer-reviews", "faq"):
        simple = ["hero", "body", "cta", "faq_or_grid", "footer"]
        return simple[min(index_in_section, len(simple) - 1)]
    return service_order[min(index_in_section, len(service_order) - 1)]


def main() -> None:
    blocks, _ = parse_document(DOCX)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    current: dict | None = None
    sections: list[dict] = []
    orphan_images: list[str] = []

    for block in blocks:
        header = match_section(block["text"])
        if header:
            html_page, key, title = header
            current = {
                "section_key": key,
                "html_page": html_page,
                "header": title,
                "text_blocks": [],
                "images": [],
            }
            sections.append(current)

        if not current:
            orphan_images.extend(block["images"])
            continue

        if block["text"] and not header:
            current["text_blocks"].append(block["text"])
        for img in block["images"]:
            current["images"].append(img)

    # annotate slots and extract files
    report_sections = []
    for sec in sections:
        imgs = []
        for i, name in enumerate(sec["images"]):
            src = f"word/media/{name}"
            dest = OUT_DIR / sec["section_key"] / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(DOCX) as zf:
                if not dest.exists():
                    dest.write_bytes(zf.read(src))
            imgs.append(
                {
                    "file": name,
                    "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                    "index_in_section": i,
                    "likely_html_slot": slot_guess(sec["section_key"], i, len(sec["images"])),
                    "nearby_text_before": sec["text_blocks"][-3:] if sec["text_blocks"] else [],
                }
            )
        report_sections.append(
            {
                "section_key": sec["section_key"],
                "html_page": sec["html_page"],
                "header": sec["header"],
                "image_count": len(imgs),
                "text_block_count": len(sec["text_blocks"]),
                "images": imgs,
                "first_text_lines": sec["text_blocks"][:6],
                "last_text_lines": sec["text_blocks"][-4:],
            }
        )

    report = {
        "docx": DOCX.name,
        "total_images": sum(s["image_count"] for s in report_sections) + len(orphan_images),
        "orphan_images_before_first_header": orphan_images,
        "sections": report_sections,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote {REPORT}")
    for s in report_sections:
        print(f"{s['html_page']:35} images={s['image_count']:2}  texts={s['text_block_count']:3}")


if __name__ == "__main__":
    main()
