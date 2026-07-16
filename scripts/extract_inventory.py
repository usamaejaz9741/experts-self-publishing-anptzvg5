"""Extract docx content into content/inventory.yaml"""
import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "Experts Self Publishing Content.docx"

SECTIONS = [
    ("home", "index.html", 0, 41),
    ("author-website", "author-website.html", 41, 75),
    ("pr-publicity", "pr-and-publicity.html", 75, 111),
    ("editing", "book-editing-proofreading.html", 111, 146),
    ("cover-design", "book-cover-design.html", 146, 185),
    ("ghostwriting", "ghostwriting.html", 185, 221),
    ("illustration", "book-illustration.html", 221, 258),
    ("video-trailer", "book-video-trailers.html", 258, 295),
    ("creative-writing", "creative-writing.html", 295, 333),
    ("children-illustration", "children-book-illustration.html", 333, 360),
    ("screenplay", "screenplay-script-writing.html", 360, 385),
    ("book-publishing", "book-publishing.html", 385, 464),
    ("book-marketing", "book-marketing.html", 464, 529),
    ("pricing", "pricing.html", 529, 534),
    ("about", "about-us.html", 534, 560),
    ("published-books", "published-books.html", 560, 576),
    ("customer-reviews", "customer-reviews.html", 576, 625),
    ("faq", "faq.html", 625, None),
]


def fix_merged_headings(text: str) -> str:
    """Insert spaces where docx lost breaks between adjacent headings."""
    patterns = [
        (r"DirectionProfessional", "Direction Professional"),
        (r"ClarityYour", "Clarity Your"),
        (r"SurprisesPackages", "Surprises\nPackages"),
        (r"QUESTIONS Common", "QUESTIONS\nCommon"),
        (r"QUESTIONS([A-Z])", r"QUESTIONS \1"),
        (r"GuidanceComplete", "Guidance\nComplete"),
        (r"ExpertiseComplete", "Expertise\nComplete"),
        (r"BlueprintComplete", "Blueprint\nComplete"),
        (r"SuccessHelp", "Success\nHelp"),
        (r"More Than Book MarketingWe", "More Than Book Marketing\nWe"),
        (r"Over 8 YearsReal", "Over 8 Years\nReal"),
        (r"ReadersProfessional", "Readers\nProfessional"),
        (r"LifeCustom", "Life\nCustom"),
        (r"SuccessTurn", "Success\nTurn"),
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


def extract_lines() -> list[str]:
    with zipfile.ZipFile(DOCX) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    text = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    text = re.sub(r"</w:p>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return [normalize(ln) for ln in text.splitlines() if ln.strip()]


def main() -> None:
    lines = extract_lines()
    data = {"sections": {}, "testimonials": []}

    for key, page, start, end in SECTIONS:
        end_idx = len(lines) if end is None else end
        paras = split_merged_paragraphs(lines[start:end_idx])
        data["sections"][key] = {
            "page": page,
            "paragraphs": paras,
        }

    # Parse structured testimonials from customer-reviews section
    cr = data["sections"]["customer-reviews"]["paragraphs"]
    reviews_start = None
    for i, p in enumerate(cr):
        if p == "What Our Clients Say About Us?":
            reviews_start = i + 2
            break
    if reviews_start:
        i = reviews_start
        current = None
        while i < len(cr) and not cr[i].startswith("Start Your Publishing Journey"):
            line = cr[i]
            if line in {
                "Author of The Fated Heir Chronicles",
            } or (line.isupper() and len(line) < 40 and "?" not in line):
                if current and current.get("body"):
                    data["testimonials"].append(current)
                current = {"name": line, "subtitle": "", "title": "", "body": []}
            elif current is not None:
                if not current["subtitle"] and line.startswith("Author of"):
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

    slot_types = {
        "home": ["meta", "hero", "services", "testimonials", "footer"],
        "pricing": ["meta", "hero", "needs_copy:package_cards"],
        "customer-reviews": ["meta", "hero", "testimonials", "cta"],
        "faq": ["meta", "accordion"],
    }

    yaml_lines = ["sections:"]
    for key, info in data["sections"].items():
        yaml_lines.append(f"  {key}:")
        yaml_lines.append(f"    page: {info['page']}")
        yaml_lines.append(f"    paragraph_count: {len(info['paragraphs'])}")
        yaml_lines.append("    status: applied")
        slots = slot_types.get(key, ["meta", "hero", "body", "faq", "footer"])
        yaml_lines.append("    slots:")
        for slot in slots:
            yaml_lines.append(f"      - {slot}")
        if key == "pricing":
            yaml_lines.append("    notes: Doc has 5 lines; HTML package cards need_copy")
    yaml_lines.append("testimonials:")
    for t in data["testimonials"]:
        yaml_lines.append(f"  - name: {json.dumps(t.get('name', ''))}")
    (out_dir / "inventory.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_dir / 'inventory.json'} ({len(data['sections'])} sections)")
    print(f"Parsed {len(data['testimonials'])} testimonials")


if __name__ == "__main__":
    main()
