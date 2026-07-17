"""Extract docx content into content/inventory.json using image-boundary slot parsing."""
from __future__ import annotations

import html
import json
import re
import zipfile
from pathlib import Path

from slot_inference import infer_slots

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "Experts Self Publishing Content (New).docx"

SECTION_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("home", "index.html", re.compile(r"^Home Page$", re.I)),
    ("author-website", "author-website.html", re.compile(r"^Services \( Athor\)$", re.I)),
    ("pr-publicity", "pr-and-publicity.html", re.compile(r"^PR & Publicity services$", re.I)),
    ("editing", "book-editing-proofreading.html", re.compile(r"^Book editing proofreading$", re.I)),
    ("cover-design", "book-cover-design.html", re.compile(r"^Book Cover Design Services$", re.I)),
    ("ghostwriting", "ghostwriting.html", re.compile(r"^Ghostwriting$", re.I)),
    ("illustration", "book-illustration.html", re.compile(r"^Book Illustration$", re.I)),
    ("video-trailer", "book-video-trailers.html", re.compile(r"^Book Video Trailer$", re.I)),
    ("creative-writing", "creative-writing.html", re.compile(r"^Creative Writing$", re.I)),
    (
        "children-illustration",
        "children-book-illustration.html",
        re.compile(r"^Children.s Book", re.I),
    ),
    (
        "screenplay",
        "screenplay-script-writing.html",
        re.compile(r"^Screenplat Script Writing$", re.I),
    ),
    ("book-publishing", "book-publishing.html", re.compile(r"^Book Publishing$", re.I)),
    ("book-marketing", "book-marketing.html", re.compile(r"^Book Marketing$", re.I)),
    ("pricing", "pricing.html", re.compile(r"^Pricing$", re.I)),
    ("about", "about-us.html", re.compile(r"^About Experts Self\s+Publishing$", re.I)),
    ("published-books", "published-books.html", re.compile(r"^RESOURCES\(PUBLIC BOOKS\)$", re.I)),
    ("customer-reviews", "customer-reviews.html", re.compile(r"^RESOURCES\(CUSTOMER REVIEWS\)$", re.I)),
    ("faq", "faq.html", re.compile(r"^FAQ$", re.I)),
]

SKIP_EXACT = {
    "Experts Self Publishing Content",
    "OUR STORY",
    "Our Journey",
    "Book Publishing",
    "Home Page",
    "Services ( Athor)",
    "PR & Publicity services",
    "Book editing proofreading",
    "Ghostwriting",
    "Book Illustration",
    "Book Video Trailer",
    "Creative Writing",
    "Book Marketing",
    "FAQ",
    "Pricing",
    "Book Cover Design Services",
    "RESOURCES(PUBLIC BOOKS)",
    "RESOURCES(CUSTOMER REVIEWS)",
    "Screenplat Script Writing",
}


def fix_merged_headings(text: str) -> str:
    """Insert spaces/newlines where docx lost breaks between adjacent headings."""
    patterns = [
        (r"WithProfessional", "With\nProfessional"),
        (r"WordsThat", "Words\nThat"),
        (r"ScreenThey", "Screen\nThey"),
        (r"HeartChildren", "Heart\nChildren"),
        (r"ConfidenceProfessional", "Confidence\nProfessional"),
        (r"Fans WithProfessional", "Fans With\nProfessional"),
        (r"SuccessBuild", "Success\nBuild"),
        (r"SuccessLet", "Success\nLet"),
        (r"SuccessTurn", "Success\nTurn"),
        (r"SuccessHelp", "Success\nHelp"),
        (r"ReadersStrategic", "Readers\nStrategic"),
        (r"SurprisesPackages", "Surprises\nPackages"),
        (r"BlueprintOur", "Blueprint\nOur"),
        (r"BlueprintComplete", "Blueprint\nComplete"),
        (r"YearsReal", "Years\nReal"),
        (r"MarketingWe", "Marketing\nWe"),
        (r"QUESTIONSCommon", "QUESTIONS\nCommon"),
        (r"QUESTIONS Common", "QUESTIONS\nCommon"),
        (r"QUESTIONS([A-Z])", r"QUESTIONS \1"),
        (r"DirectionProfessional", "Direction Professional"),
        (r"ClarityYour", "Clarity Your"),
        (r"GuidanceComplete", "Guidance\nComplete"),
        (r"ExpertiseComplete", "Expertise\nComplete"),
        (r"More Than Book MarketingWe", "More Than Book Marketing\nWe"),
        (r"Over 8 YearsReal", "Over 8 Years\nReal"),
        (r"ReadersProfessional", "Readers\nProfessional"),
        (r"LifeCustom", "Life\nCustom"),
        (r"RoadmapOur", "Roadmap\nOur"),
        (r"ExperienceReal", "Experience\nReal"),
        (r"IllustrationsProfessional", "Illustrations\nProfessional"),
        (r"ScreenplayProfessional", "Screenplay\nProfessional"),
        (r"PublisherYour", "Publisher\nYour"),
        (r"StepWe", "Step\nWe"),
        (r"ListenOur", "Listen\nOur"),
        (r"TrustWith", "Trust\nWith"),
        (r"CareEvery", "Care\nEvery"),
        (r"StartedTake", "Started\nTake"),
        (r"DiscussionA", "Discussion\nA"),
        (r"PlanningOur", "Planning\nOur"),
        (r"ReviewEach", "Review\nEach"),
        (r"PromotionAfter", "Promotion\nAfter"),
        (r"LoveOur", "Love\nOur"),
        (r"place\.Your", "place. Your"),
        (r"publication\.A", "publication. A"),
        (r"ScrollBook", "Scroll\nBook"),
        (r"PageCustom", "Page\nCustom"),
        (r"Imagination From", "Imagination\nFrom"),
        (r"IllustrationsBring", "Illustrations\nBring"),
    ]
    for pattern, repl in patterns:
        text = re.sub(pattern, repl, text)
    return text


def normalize(text: str) -> str:
    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\ufffd", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    text = re.sub(r"UBP's", "Experts Self Publishing's", text, flags=re.I)
    text = re.sub(r"\bUBP\b", "Experts Self Publishing", text)
    text = re.sub(r"United Book Publishing", "Experts Self Publishing", text)
    text = re.sub(r"\bExpert Self Publishing\b", "Experts Self Publishing", text)
    text = fix_merged_headings(text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text


def split_merged_paragraphs(paras: list[str]) -> list[str]:
    out: list[str] = []
    for p in paras:
        if "\n" in p:
            out.extend(part.strip() for part in p.split("\n") if part.strip())
        else:
            out.append(p)
    return out


def parse_blocks(docx: Path) -> list[dict]:
    with zipfile.ZipFile(docx) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")

    rid_to_media: dict[str, str] = {}
    for match in re.finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels_xml):
        rid_to_media[match.group(1)] = match.group(2)

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


def match_section(text: str) -> tuple[str, str] | None:
    for key, page, pattern in SECTION_PATTERNS:
        if pattern.match(text):
            return key, page
    if re.match(r"^Children.s Book", text, re.I):
        return "children-illustration", "children-book-illustration.html"
    return None


def text_chunks_from_section(section_blocks: list[dict]) -> list[list[str]]:
    """Group text paragraphs that follow each in-flow image (image-delimited slots)."""
    chunks: list[list[str]] = []
    current: list[str] = []
    for block in section_blocks:
        text = block["text"]
        if text in SKIP_EXACT or match_section(text):
            continue
        if block["images"] and current:
            chunks.append(current)
            current = []
        if text:
            current.append(text)
    if current:
        chunks.append(current)
    return chunks


def home_chunks_before_first_service(blocks: list[dict], home_idx: int, next_idx: int) -> list[list[str]]:
    """Home uses fewer in-flow images; split on images between Home Page and Services header."""
    section = blocks[home_idx:next_idx]
    chunks = text_chunks_from_section(section)
    if not chunks and section:
        pre_image: list[str] = []
        for block in section:
            if block["text"] in SKIP_EXACT or match_section(block["text"]):
                continue
            if block["images"]:
                if pre_image:
                    chunks.append(pre_image)
                    pre_image = []
                continue
            if block["text"]:
                pre_image.append(block["text"])
        if pre_image:
            chunks.insert(0, pre_image)
    return chunks


def section_ranges(blocks: list[dict]) -> list[tuple[str, str, int, int]]:
    headers: list[tuple[str, str, int]] = []
    for i, block in enumerate(blocks):
        if not block["text"]:
            continue
        hit = match_section(block["text"])
        if hit:
            headers.append((hit[0], hit[1], i))
    ranges: list[tuple[str, str, int, int]] = []
    for j, (key, page, start) in enumerate(headers):
        end = headers[j + 1][2] if j + 1 < len(headers) else len(blocks)
        ranges.append((key, page, start, end))
    return ranges


def main() -> None:
    blocks = parse_blocks(DOCX)
    ranges = section_ranges(blocks)
    data: dict = {"sections": {}, "testimonials": [], "source_docx": DOCX.name}

    for key, page, start, end in ranges:
        section_blocks = blocks[start:end]
        if key == "home":
            chunks = home_chunks_before_first_service(blocks, start, end)
        else:
            chunks = text_chunks_from_section(section_blocks)

        split_chunks = [split_merged_paragraphs(chunk) for chunk in chunks]
        paragraphs = [p for chunk in split_chunks for p in chunk]
        slots = infer_slots(page, split_chunks)

        data["sections"][key] = {
            "page": page,
            "paragraphs": paragraphs,
            "image_chunks": split_chunks,
            "image_count": sum(1 for b in section_blocks if b["images"]),
            "slots": slots,
        }

    cr = data["sections"].get("customer-reviews", {}).get("paragraphs", [])
    reviews_start = None
    for i, p in enumerate(cr):
        if p == "What Our Clients Say About Us?":
            reviews_start = i + 2
            break
    if reviews_start:
        names = [
            "Barbara Pennington, PhD",
            "Mikhaila Thorne",
            "Bruce",
            "Paul Rollins",
            "Alina Dubrova",
            "Julian Hutchinson",
            "Tanya D. McIntire",
            "Pamela Drake",
        ]
        i = reviews_start
        current = None
        while i < len(cr) and not cr[i].startswith("Start Your Publishing Journey"):
            line = cr[i]
            if line in names:
                if current and current.get("body"):
                    data["testimonials"].append(current)
                current = {"name": line, "subtitle": "", "title": "", "body": []}
            elif current is not None:
                if line.startswith("Author of"):
                    current["subtitle"] = line
                elif not current["title"] and len(line) < 80 and i + 1 < len(cr) and len(cr[i + 1]) > 80:
                    current["title"] = line
                else:
                    current["body"].append(line)
            i += 1
        if current and current.get("body"):
            data["testimonials"].append(current)

    out_dir = ROOT / "content"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "inventory.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    slots_path = out_dir / "page-slots.json"
    page_slots = {info["page"]: info["slots"] for info in data["sections"].values() if info.get("slots")}
    slots_path.write_text(json.dumps(page_slots, indent=2, ensure_ascii=False), encoding="utf-8")

    yaml_lines = ["sections:"]
    for key, info in data["sections"].items():
        yaml_lines.append(f"  {key}:")
        yaml_lines.append(f"    page: {info['page']}")
        yaml_lines.append(f"    paragraph_count: {len(info['paragraphs'])}")
        yaml_lines.append(f"    image_count: {info['image_count']}")
        yaml_lines.append(f"    chunk_count: {len(info['image_chunks'])}")
        yaml_lines.append("    status: image-slotted")
    (out_dir / "inventory.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_dir / 'inventory.json'} ({len(data['sections'])} sections)")
    print(f"Wrote {slots_path}")
    for key, info in data["sections"].items():
        print(f"  {info['page']:35} paras={len(info['paragraphs']):3} chunks={len(info['image_chunks']):2} imgs={info['image_count']:2}")


if __name__ == "__main__":
    main()
