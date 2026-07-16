"""Apply content from content/inventory.json to core HTML pages (text-only, slot-based)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from page_slots import PAGE_SLOTS

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "content" / "inventory.json"

CORE_PAGES = [
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

COPYRIGHT_SNIPPETS = [
    (
        "Copyright © 2026 United Book Publishing - All Rights Reserved | Powered By\n"
        "                    Iota Digital, LLC",
        "Copyright © 2026 Experts Self Publishing. All rights reserved.",
    ),
    (
        "Copyright © 2026 United Book Publishing - All Rights Reserved | Powered By Iota Digital, LLC",
        "Copyright © 2026 Experts Self Publishing. All rights reserved.",
    ),
]

FOOTER_ABOUT = (
    (
        "For 8+ years, we have been the quiet force behind unforgettable stories. We\n"
        "                        don't just publish books; we partner with visionaries, transforming bold ideas into legacies\n"
        "                        that endure. Let us build yours.",
        "Publishing a book should feel exciting, not overwhelming. We support authors with editing, design, publishing, websites, marketing, and practical guidance from manuscript to marketplace.",
    ),
)

TESTIMONIALS = [
    {
        "name": "Barbara Pennington, PhD",
        "title": "An outstanding publishing experience",
        "body": "Turning my years of work as an educational psychologist into a compelling book was a long-held goal. Mike and Aron, along with the entire team, brought the expertise and creativity needed to make that vision a reality. Working together on Designing Learning Journeys was an outstanding experience. Their professionalism, attention to detail, creative approach, and genuine support exceeded my expectations, making the entire publishing process both smooth and memorable.",
    },
    {
        "name": "Mikhaila Thorne",
        "title": "Author of The Fated Heir Chronicles",
        "body": "Even in the early stages, the team's dedication and hard work have given me complete confidence in the publishing process. Alex and Aaron have been supportive, knowledgeable, and responsive, making every step feel straightforward and well managed. Having invested so much into my novels, I'm grateful to have a team that truly understands my vision. Their professionalism and commitment have made this journey rewarding, and I'm excited to see my stories reach readers.",
    },
    {
        "name": "Bruce",
        "title": "A rewarding first publishing experience",
        "body": "As a first-time author, I appreciated the team's professionalism, industry knowledge, and patience throughout the publishing process. They also worked closely with my illustrator to ensure the artwork met publishing standards. It was a rewarding experience, and I'm thankful for the dedication and support I received from the entire team.",
    },
    {
        "name": "Paul Rollins",
        "title": "Professional and flexible support",
        "body": "Mike and Aron were attentive, welcomed my feedback, and stayed focused on producing the best possible book. Their flexibility, professionalism, and commitment to quality made the publishing experience smooth and enjoyable. I highly recommend their services to any author looking for a reliable publishing partner.",
    },
    {
        "name": "Alina Dubrova",
        "title": "Stress-free publishing support",
        "body": "Working with this publishing team was a wonderful experience. They paid close attention to every detail and guided me through each stage with care and professionalism. Their communication was always clear, patient, and honest, making the entire process stress-free. I also appreciated their flexible pricing and genuine commitment to helping authors succeed. I would confidently choose them again for future publishing projects.",
    },
    {
        "name": "Julian Hutchinson",
        "title": "One of my best publishing experiences",
        "body": "My publishing journey had a difficult beginning, but everything improved once my account was assigned to a dedicated manager. The team quickly resolved the issues, republished my book with great care, and delivered results that exceeded my expectations. After publishing several books over the years, I can confidently say this has been one of my best experiences.",
    },
    {
        "name": "Tanya D. McIntire",
        "title": "Supportive from start to finish",
        "body": "The team remained supportive and informative throughout the entire publishing process. They listened carefully to my ideas, created a cover that reflected my vision, and ensured every detail matched what I had imagined. I'm extremely pleased with the final result.",
    },
    {
        "name": "Pamela Drake",
        "title": "Clear guidance throughout",
        "body": "The professionalism and guidance I received made the publishing process easy to understand. Every question was answered with patience, and I felt supported from beginning to end. The reassurance, attention to detail, and quality of the finished book left me completely satisfied with the overall experience.",
    },
]

SKIP_LABELS = {
    "AUTHOR",
    "FREQUENTLY ASKED QUESTIONS",
    "PR & Publicity services",
    "Book editing proofreading",
    "Ghostwriting",
    "Book Illustration",
    "Book Video Trailer",
    "Creative Writing",
    "Book Publishing",
    "Book Marketing",
    "FAQ",
    "OUR STORY",
    "RESOURCES(PUBLIC BOOKS)",
    "RESOURCES(CUSTOMER REVIEWS)",
    "Experts Self Publishing Content",
    "Pricing",
    "Book Cover Design Services",
}

def skip_body_paragraph(p: str) -> bool:
    if p in SKIP_LABELS:
        return True
    if p.startswith("FREQUENTLY ASKED"):
        return True
    if p.startswith("Your Vision"):
        return True
    # Skip cross-page vision headings but keep book-publishing benefit titles.
    if p.startswith("Complete Publishing") and "Support" not in p:
        return True
    return False


def sequential_body_paragraphs(paragraphs: list[str]) -> list[str]:
    """Doc body copy in order, excluding labels, FAQ blocks, and vision boilerplate."""
    out: list[str] = []
    fi = faq_start(paragraphs)
    for i, p in enumerate(paragraphs):
        if i >= fi:
            break
        if skip_body_paragraph(p):
            continue
        out.append(p)
    return out


def load_inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def looks_like_splittable_heading(text: str) -> bool:
    if is_short_heading(text):
        return True
    if len(text) >= 100 or text.count(".") >= 2:
        return False
    if text.endswith(".") and len(text) > 70:
        return False
    return True


def split_heading_two_line(text: str) -> tuple[str, str]:
    if not looks_like_splittable_heading(text):
        return text.strip(), ""
    for sep in (" with ", " Over ", " - "):
        if sep in text:
            left, right = text.split(sep, 1)
            if len(left) < 80:
                suffix = sep.strip()
                return left.strip(), f"{suffix} {right.strip()}"
    if " Professional " in text:
        left, right = text.split(" Professional ", 1)
        if len(left) < 80:
            return left.strip(), f"Professional {right.strip()}"
    if " Your " in text and text.index(" Your ") > 10:
        left, right = text.split(" Your ", 1)
        if len(left) < 80:
            return left.strip(), f"Your {right.strip()}"
    return text.strip(), ""


def faq_start(paragraphs: list[str]) -> int:
    for i, p in enumerate(paragraphs):
        if p.startswith("FREQUENTLY ASKED") or p == "FAQ":
            return i
    return len(paragraphs)


def is_short_heading(p: str) -> bool:
    return len(p) < 70 and not p.endswith(".") and "?" not in p


def consume_heading_pair(seq: list[str], idx: int) -> tuple[str, str, int]:
    if idx >= len(seq):
        return "", "", idx
    if idx + 1 < len(seq) and is_short_heading(seq[idx]) and is_short_heading(seq[idx + 1]):
        return seq[idx], seq[idx + 1], idx + 2
    text = seq[idx]
    if looks_like_splittable_heading(text):
        top, sub = split_heading_two_line(text)
        if sub or is_short_heading(top):
            return top, sub, idx + 1
    return "", "", idx


def set_text(el, text: str) -> None:
    if el is None:
        return
    el.clear()
    if text:
        el.append(text)


def extract_faq_pairs(paragraphs: list[str]) -> list[tuple[str, str]]:
    fi = faq_start(paragraphs)
    if fi >= len(paragraphs):
        for i, p in enumerate(paragraphs):
            if p.startswith("Answers With") or p.startswith("Answers with"):
                fi = i
                break
    header = paragraphs[fi] if fi < len(paragraphs) else ""
    if header.startswith("FREQUENTLY ASKED QUESTIONS ") and len(header) > len("FREQUENTLY ASKED QUESTIONS "):
        start = fi + 2
    elif header in {"FREQUENTLY ASKED QUESTIONS", "FAQ"}:
        start = fi + 3
    elif header.startswith("Answers With") or header.startswith("Answers with"):
        start = fi + 2
    else:
        start = fi + 2
    pairs: list[tuple[str, str]] = []
    for i in range(start, len(paragraphs)):
        p = paragraphs[i]
        if "?" in p and len(p) < 220:
            if i + 1 < len(paragraphs) and "?" not in paragraphs[i + 1][:80]:
                pairs.append((p, paragraphs[i + 1]))
    return pairs


def apply_faq_section(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    fi = faq_start(paragraphs)
    faq_sec = soup.select_one("section.faq-sec, section.accordion-sec")
    if not faq_sec or fi >= len(paragraphs):
        return
    set_text(faq_sec.select_one(".font-35"), "FREQUENTLY ASKED QUESTIONS")
    header = paragraphs[fi]
    if header.startswith("FREQUENTLY ASKED QUESTIONS ") and len(header) > len("FREQUENTLY ASKED QUESTIONS "):
        faq_title = header.replace("FREQUENTLY ASKED QUESTIONS", "").strip()
        faq_intro = paragraphs[fi + 1] if fi + 1 < len(paragraphs) else ""
    elif header in {"FREQUENTLY ASKED QUESTIONS", "FAQ"}:
        faq_title = paragraphs[fi + 1] if fi + 1 < len(paragraphs) else ""
        faq_intro = paragraphs[fi + 2] if fi + 2 < len(paragraphs) else ""
    else:
        faq_title = header
        faq_intro = paragraphs[fi + 1] if fi + 1 < len(paragraphs) else ""
    set_text(faq_sec.select_one("h2.sec-hd"), faq_title)
    intro = faq_sec.select_one("p.para-color, p.reveal, p.w-80, .faq-heading p")
    if intro:
        set_text(intro, faq_intro)
    apply_faq(soup, extract_faq_pairs(paragraphs))


def first_long_para(paragraphs: list[str]) -> str:
    for p in sequential_body_paragraphs(paragraphs):
        if len(p) > 80:
            return p
    return "Experts Self Publishing"


def meta_title(paragraphs: list[str]) -> str:
    for p in sequential_body_paragraphs(paragraphs)[:4]:
        if 15 < len(p) < 90 and not p.endswith("."):
            return p
    seq = sequential_body_paragraphs(paragraphs)
    return seq[0][:80] if seq else "Experts Self Publishing"


def apply_meta(soup: BeautifulSoup, title: str, description: str) -> None:
    if soup.title:
        soup.title.string = f"{title} | Experts Self Publishing"
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        meta["content"] = description[:300]


def apply_globals_raw(html: str) -> str:
    html = html.replace('alt="Unitedbookpublishing"', 'alt="Experts Self Publishing"')
    html = html.replace('alt="massege"', 'alt="Experts Self Publishing"')
    html = re.sub(r"\bUBP\b", "Experts Self Publishing", html)
    html = re.sub(r"\bExpert Self Publishing\b", "Experts Self Publishing", html)
    for old, new in COPYRIGHT_SNIPPETS:
        html = html.replace(old, new)
    for old, new in FOOTER_ABOUT:
        html = html.replace(old, new)
    return html


def apply_faq(soup: BeautifulSoup, pairs: list[tuple[str, str]]) -> None:
    buttons = soup.select("section.faq-sec .accordion-button, section.accordion-sec .accordion-button")
    bodies = soup.select("section.faq-sec .accordion-body, section.accordion-sec .accordion-body")
    for i, (q, a) in enumerate(pairs):
        if i < len(buttons):
            set_text(buttons[i], q)
        if i < len(bodies):
            p = bodies[i].find("p")
            set_text(p or bodies[i], a)


def apply_testimonial_boxes(soup: BeautifulSoup, testimonials: list[dict]) -> None:
    boxes = soup.select(".testimonial-slider .testimonial-box")
    for i, box in enumerate(boxes):
        t = testimonials[i % len(testimonials)]
        set_text(box.select_one(".profile-d h4"), t["name"])
        set_text(box.select_one(".testi-para strong"), t["title"])
        paras = box.select(".testi-para p")
        if paras:
            set_text(paras[0], t["body"])
            for p in paras[1:]:
                p.decompose()
        circle = box.select_one(".name-1")
        if circle and t["name"]:
            parts = [x for x in re.split(r"[\s,]+", t["name"]) if x and x.lower() not in {"phd", "author", "of"}]
            circle.string = "".join(w[0].upper() for w in parts[:2])


def is_faq_header(p: str) -> bool:
    return (
        p.startswith("Answers With")
        or p.startswith("Common Questions")
        or ("Questions" in p and "Answered" in p)
        or (p.startswith("FREQUENTLY") and "QUESTIONS" in p)
    )


def para_at(paragraphs: list[str], idx: int | str) -> str:
    if idx == "overflow":
        return ""
    if not isinstance(idx, int) or idx < 0 or idx >= len(paragraphs):
        return ""
    return paragraphs[idx]


def apply_from_slots(soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> None:
    """Map inventory paragraph indices to named HTML slots."""
    hero = slots.get("hero", [])
    hero_sels = (
        ".inner-heading .font-35, .about-banner .font-35",
        ".main-heading, .bann-heading h1",
        ".inner-heading > p, .inner-heading p.reveal, .about-banner p.reveal",
    )
    for sel, idx in zip(hero_sels, hero):
        el = soup.select_one(sel)
        if el:
            set_text(el, para_at(paragraphs, idx))

    box = soup.select_one("section.about-1 .content-box")
    overflow = ""
    if box:
        if slots.get("content_heading_empty"):
            set_text(box.select_one(".font-35"), "")
            set_text(box.select_one("h2.sec-hd"), "")
        elif "content_heading_split" in slots:
            a, b = slots["content_heading_split"]
            set_text(box.select_one(".font-35"), para_at(paragraphs, a))
            set_text(box.select_one("h2.sec-hd"), para_at(paragraphs, b))
        elif "content_heading" in slots:
            text = para_at(paragraphs, slots["content_heading"])
            top, sub = split_heading_two_line(text)
            set_text(box.select_one(".font-35"), top)
            set_text(box.select_one("h2.sec-hd"), sub)

        intro_idx = slots.get("content_intro")
        if intro_idx is not None:
            text = para_at(paragraphs, intro_idx)
            sents = split_sentences(text)
            intro = box.select_one("p.para-color")
            if intro:
                set_text(intro, sents[0] if sents else text)
            if len(sents) > 1:
                overflow = " ".join(sents[1:])

    content_els = soup.select("section.about-1 .content p.para-color")
    for el in content_els:
        set_text(el, "")
    for i, el in enumerate(content_els):
        rows = slots.get("content_rows", [])
        if i >= len(rows):
            break
        spec = rows[i]
        if spec == "overflow":
            set_text(el, overflow)
        else:
            set_text(el, para_at(paragraphs, spec))

    if not slots.get("cta_no_doc"):
        cta = soup.select_one("section.cta-sec .cta-content")
        if cta:
            if fixed := slots.get("cta_h3_fixed"):
                set_text(cta.select_one("h3.bg-rect"), fixed)
            cta_slots = slots.get("cta", [])
            cta_sels = ("h3.bg-rect", "h2.sec-hd", "p")
            start = 1 if slots.get("cta_h3_fixed") else 0
            for j, sel in enumerate(cta_sels[start:]):
                if j >= len(cta_slots):
                    break
                el = cta.select_one(sel)
                if el:
                    set_text(el, para_at(paragraphs, cta_slots[j]))

    make = soup.select_one("section.make-unique .make-content")
    if make and "make_title" in slots:
        title = para_at(paragraphs, slots["make_title"])
        h2 = make.select_one("h2")
        if h2 and title:
            set_text(h2, title)
        for el in make.select("p.para-color"):
            set_text(el, "")
        for el, idx in zip(make.select("p.para-color"), slots.get("make_body", [])):
            set_text(el, para_at(paragraphs, idx))

    apply_faq_section(soup, paragraphs)


def apply_standard_service_page(soup: BeautifulSoup, paragraphs: list[str], page: str) -> None:
    """Fill the shared service-page template from PAGE_SLOTS manifest."""
    slots = PAGE_SLOTS.get(page, {})
    if slots and not slots.get("type"):
        apply_from_slots(soup, paragraphs, slots)



def set_li_text(el, text: str) -> None:
    icon = el.select_one("i")
    el.clear()
    if icon:
        el.append(icon)
        el.append(NavigableString(" " + text))
    else:
        set_text(el, text)


def apply_book_publishing(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    slots = PAGE_SLOTS["book-publishing.html"]

    for sel, idx in (
        (".bann-heading h1", slots["banner"][0]),
        (".bann-heading > p.text-white", slots["banner"][1]),
    ):
        el = soup.select_one(sel)
        if el:
            set_text(el, para_at(paragraphs, idx))

    s1 = soup.select_one("section.book-publishing-sec .s1-left")
    if s1:
        top, sub, _ = consume_heading_pair(paragraphs, slots["s1_heading"])
        set_text(s1.select_one(".font-35"), top)
        set_text(s1.select_one("h2.sec-hd"), sub)
        for el, idx in zip(s1.select("p")[:3], slots["s1_body"]):
            set_text(el, para_at(paragraphs, idx))

    cta = soup.select_one("section.cta-sec .cta-content")
    if cta:
        set_text(cta.select_one("h3.bg-rect"), slots["cta_h3_fixed"])
        set_text(cta.select_one("h2.sec-hd"), para_at(paragraphs, slots["cta"][0]))
        set_text(cta.select_one("p"), para_at(paragraphs, slots["cta"][1]))

    kdp = slots["kdp"]
    kdp_el = soup.select_one("section.kdp-sec .kdp-content")
    if kdp_el:
        set_text(kdp_el.select_one("h2.sec-hd"), para_at(paragraphs, kdp["heading"]))
        direct_ps = [c for c in kdp_el.children if getattr(c, "name", None) == "p"]
        intro = kdp["intro"]
        closing = kdp["closing"]
        if len(direct_ps) >= 4:
            set_text(direct_ps[0], para_at(paragraphs, intro[0]))
            set_text(direct_ps[1], para_at(paragraphs, intro[1]))
            set_text(direct_ps[2], para_at(paragraphs, closing[0]))
            set_text(direct_ps[3], para_at(paragraphs, closing[1]))
        for el, idx in zip(kdp_el.select("ul li"), kdp["bullets"]):
            set_li_text(el, para_at(paragraphs, idx))

    sk = slots["self_kdp"]
    self_sec = soup.select_one("section.self-kdp")
    if self_sec:
        set_text(self_sec.select_one(".self-heading h2"), para_at(paragraphs, sk["heading"]))
        set_text(self_sec.select_one(".self-heading p"), para_at(paragraphs, sk["intro"]))
        for bt, (ti, bi) in zip(self_sec.select(".benefit-text"), sk["benefits"]):
            set_text(bt.select_one("strong"), para_at(paragraphs, ti))
            set_text(bt.select_one("span"), para_at(paragraphs, bi))

    p1 = slots["publish_1"]
    pub = soup.select_one("section.publish-1 .publish-heading")
    if pub:
        set_text(pub.select_one("h2.sec-hd"), para_at(paragraphs, p1["heading"]))
        for el, idx in zip(pub.select("p")[:2], p1["body"]):
            set_text(el, para_at(paragraphs, idx))

    testi = soup.select_one(".testi-heading")
    if testi:
        ti = slots["testi"]
        set_text(testi.select_one(".font-35"), para_at(paragraphs, ti[0]))
        set_text(testi.select_one(".sec-hd"), para_at(paragraphs, ti[1]))
        set_text(testi.select_one("p"), para_at(paragraphs, ti[2]))

    fi = faq_start(paragraphs)
    faq_sec = soup.select_one("section.faq-sec, section.accordion-sec")
    if faq_sec and fi + 2 < len(paragraphs):
        set_text(faq_sec.select_one("h2.sec-hd"), paragraphs[fi + 1])
        intro = faq_sec.select_one("p.para-color, p.reveal")
        if intro:
            set_text(intro, paragraphs[fi + 2])
    apply_faq(soup, extract_faq_pairs(paragraphs))


def apply_shared_services_section(soup: BeautifulSoup, home_paragraphs: list[str]) -> None:
    """Update sitewide cross-sell block (.our-service-hd) from home inventory."""
    svc = soup.select_one(".our-service-hd")
    if not svc:
        return
    usable = [p for p in home_paragraphs if p not in SKIP_LABELS and p != "Experts Self Publishing Content"]
    if len(usable) <= 10:
        return
    set_text(svc.select_one(".font-35"), usable[7])
    set_text(svc.select_one("h2.sec-hd"), usable[8])
    set_text(svc.select_one("p.para-color"), f"{usable[9]} {usable[10]}")


def apply_index_updates(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    slots = PAGE_SLOTS["index.html"]
    usable = [p for p in paragraphs if p not in SKIP_LABELS and p != "Experts Self Publishing Content"]

    for sel, idx in zip(
        (".bann-heading h1.first-content", ".bann-heading h2.bann-hd", ".bann-heading .main-para"),
        slots["hero"],
    ):
        set_text(soup.select_one(sel), para_at(usable, idx - 1))

    pub = soup.select_one(".publish-sec .s1-left")
    ps = slots["publish_sec"]
    if pub:
        partner = para_at(usable, ps["heading"] - 1)
        if "Self-Publishing Partner" in partner:
            set_text(pub.select_one(".font-35"), partner.split("Self-Publishing")[0].strip())
            set_text(pub.select_one("h2.sec-hd"), "Self-Publishing Partner?")
        for el, idx in zip(pub.select("p.reveal"), ps["body"]):
            set_text(el, para_at(usable, idx - 1))

    apply_shared_services_section(soup, paragraphs)

    cta = soup.select_one(".connect-sec .cta-left")
    conn = slots["connect"]
    if cta:
        set_text(cta.select_one(".font-45"), conn["fixed_h3"])
        set_text(cta.select_one("h2.sec-hd"), conn["fixed_h2"])
        for el, idx in zip(cta.select("p"), conn["body"]):
            set_text(el, para_at(usable, idx - 1))

    choose = soup.select_one(".why-choose-sec .choose-heading")
    wc = slots["why_choose"]
    if choose:
        set_text(choose.select_one(".font-35"), para_at(usable, wc["heading"][0] - 1))
        set_text(choose.select_one("h2.sec-hd"), para_at(usable, wc["heading"][1] - 1))
        set_text(choose.select_one("p.w-80"), f"{para_at(usable, wc['intro'][0] - 1)} {para_at(usable, wc['intro'][1] - 1)}")

    for box, (ti, bi) in zip(soup.select(".why-choose-sec .choose-box"), wc["boxes"]):
        set_text(box.select_one("h3"), para_at(usable, ti - 1))
        set_text(box.select_one("p"), para_at(usable, bi - 1))

    set_text(soup.select_one(".testi-heading .font-35"), "Trusted by Authors for Over 8 Years")
    set_text(soup.select_one(".testi-heading .sec-hd"), "Real Stories. Real Success.")
    intro = soup.select_one(".testi-heading p.w-80")
    if intro:
        set_text(intro, para_at(usable, slots["testi_intro"] - 1))


def apply_book_marketing(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    seq = sequential_body_paragraphs(paragraphs)
    idx = 0

    def take() -> str:
        nonlocal idx
        if idx >= len(seq):
            return ""
        text = seq[idx]
        idx += 1
        return text

    h1 = soup.select_one(".inner-banner .bann-heading h1")
    sub = soup.select_one(".inner-banner .bann-heading > p.text-white")
    if h1:
        set_text(h1, take())
    if sub:
        set_text(sub, take())

    for box in soup.select(".inner-banner .bann-box"):
        title, body = take(), take()
        h4 = box.select_one("h4")
        p = box.select_one(".box-content p")
        if h4 and title:
            set_text(h4, title)
        if p and body:
            set_text(p, body)

    deliver_idx = next(
        (i for i, p in enumerate(seq) if "for Self Published Authors Deliver Results" in p),
        idx,
    )
    idx = deliver_idx
    s1 = soup.select_one(".s1-left")
    if s1 and idx < len(seq):
        set_text(s1.select_one(".font-35"), "")
        set_text(s1.select_one("h2.sec-hd"), take())
        for el in s1.select("p"):
            text = take()
            if text:
                set_text(el, text)

    cta = soup.select_one("section.cta-sec .cta-content")
    if cta:
        for sel in ("h3.bg-rect", "h2.sec-hd", "p"):
            el = cta.select_one(sel)
            if not el:
                continue
            text = take()
            if text:
                set_text(el, text)

    service = soup.select_one("section.inner-service .service-heading")
    if service:
        set_text(service.select_one("h2.sec-hd"), take())
        intro = service.select_one("p")
        if intro:
            set_text(intro, take())
    for box in soup.select("section.inner-service .market-box"):
        title, body = take(), take()
        h3 = box.select_one("h3")
        p = box.select_one(".market-content p")
        if h3 and title:
            set_text(h3, title)
        if p and body:
            set_text(p, body)

    process = soup.select_one("section.process-tab-sec .process-heading")
    if process:
        set_text(process.select_one(".font-35"), "")
        set_text(process.select_one("h2.sec-hd"), take())
        intro = process.select_one("p")
        if intro:
            set_text(intro, take())

    testi = soup.select_one(".testi-heading")
    if testi and idx < len(seq):
        top, sub, new_idx = consume_heading_pair(seq, idx)
        set_text(testi.select_one(".font-35"), top)
        set_text(testi.select_one(".sec-hd"), sub)
        idx = new_idx if new_idx > idx else idx + 1
        intro = testi.select_one("p.w-80, p")
        if intro and idx < len(seq):
            set_text(intro, take())

    why = soup.select_one("section.why-choose-sec .choose-heading")
    if why and idx < len(seq):
        top, sub, new_idx = consume_heading_pair(seq, idx)
        set_text(why.select_one(".font-35"), top)
        set_text(why.select_one("h2.sec-hd"), sub)
        idx = new_idx if new_idx > idx else idx + 1
        intro = why.select_one("p.w-80")
        if intro:
            set_text(intro, take())
    for box in soup.select("section.why-choose-sec .choose-box"):
        h3 = box.select_one("h3")
        p = box.select_one("p")
        title, body = take(), take()
        if h3 and title:
            set_text(h3, title)
        if p and body:
            set_text(p, body)

    apply_faq_section(soup, paragraphs)


def apply_pricing(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    usable = [p for p in paragraphs if p not in {"Pricing", "OUR STORY", "Our Journey"}]
    banner = soup.select_one(".about-banner .inner-heading, .inner-banner .inner-heading")
    if not banner or not usable:
        return
    body_idx = 1
    if len(usable) > 1 and usable[1].startswith("Packages"):
        set_text(banner.select_one(".font-35"), usable[0])
        set_text(banner.select_one(".main-heading"), usable[1])
        body_idx = 2
    else:
        merged = usable[0]
        match = re.match(r"(.+?)\s+Packages\s+(.+)", merged)
        if match:
            set_text(banner.select_one(".font-35"), match.group(1).strip())
            set_text(banner.select_one(".main-heading"), f"Packages {match.group(2).strip()}")
        else:
            set_text(banner.select_one(".font-35"), usable[0])
    if len(usable) > body_idx:
        set_text(banner.select_one("p"), usable[body_idx])


def apply_about(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    slots = PAGE_SLOTS["about-us.html"]
    banner = soup.select_one(".about-banner .inner-heading")
    if banner:
        set_text(banner.select_one(".font-35"), slots.get("banner_fixed_label", "Our Journey"))
        set_text(banner.select_one(".main-heading"), para_at(paragraphs, slots["banner"][0]))
        intro = banner.select_one("p.reveal, p")
        if intro:
            set_text(intro, para_at(paragraphs, slots["banner"][1]))

    box = soup.select_one("section.about-1 .content-box")
    if box:
        text = para_at(paragraphs, slots["about_heading"])
        top, sub = split_heading_two_line(text)
        set_text(box.select_one(".font-35"), top)
        set_text(box.select_one("h2.sec-hd"), sub)
        intro = box.select_one("p.para-color")
        if intro:
            set_text(intro, para_at(paragraphs, slots["about_intro"]))

    for el, idx in zip(soup.select("section.about-1 .content p.para-color")[:3], slots["about_rows"]):
        set_text(el, para_at(paragraphs, idx))

    cta = soup.select_one("section.cta-sec .cta-content")
    if cta:
        for sel, idx in zip(("h3.bg-rect", "h2.sec-hd", "p"), slots["cta"]):
            set_text(cta.select_one(sel), para_at(paragraphs, idx))


def apply_published_books(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    slots = PAGE_SLOTS["published-books.html"]
    for sel, idx in zip((".font-35", ".main-heading", "p.reveal, p"), slots["banner"]):
        el = soup.select_one(f".inner-heading {sel}, .about-banner {sel}")
        if el:
            set_text(el, para_at(paragraphs, idx))


def parse_customer_review_testimonials(paragraphs: list[str]) -> list[dict]:
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
    start = 0
    for i, p in enumerate(paragraphs):
        if p == "What Our Clients Say About Us?":
            start = i + 2
            break
    testimonials: list[dict] = []
    i = start
    while i < len(paragraphs):
        line = paragraphs[i]
        if line.startswith("Start Your Publishing Journey"):
            break
        if line in names:
            body: list[str] = []
            subtitle = ""
            i += 1
            while i < len(paragraphs) and paragraphs[i] not in names and not paragraphs[i].startswith("Start Your"):
                if paragraphs[i].startswith("Author of"):
                    subtitle = paragraphs[i]
                else:
                    body.append(paragraphs[i])
                i += 1
            testimonials.append({"name": line, "subtitle": subtitle, "body": body})
            continue
        i += 1
    return testimonials or TESTIMONIALS


def apply_customer_reviews_blocks(soup: BeautifulSoup, testimonials: list[dict]) -> None:
    for block, t in zip(soup.select(".testimonials-sec"), testimonials):
        set_text(block.select_one("h4 b, h4"), t.get("name", ""))
        body_parts = t.get("body", [])
        container = block.select_one(".testi_para")
        if container:
            for child in container.find_all("p"):
                child.decompose()
            for part in body_parts:
                p = soup.new_tag("p")
                p.string = part
                container.append(p)
            if t.get("subtitle"):
                p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = t["subtitle"]
                p.append(strong)
                container.append(p)
        elif body_parts:
            for p_el in block.select("p"):
                if not p_el.find_parent("h4"):
                    set_text(p_el, body_parts[0])
                    break


def apply_customer_reviews(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    slots = PAGE_SLOTS["customer-reviews.html"]
    for sel, idx in zip((".font-35", ".main-heading", "p"), slots["banner"]):
        el = soup.select_one(f".inner-heading {sel}")
        if el:
            set_text(el, para_at(paragraphs, idx))
    set_text(soup.select_one(".our-book-sec .sec-hd"), para_at(paragraphs, slots["books_heading"]))
    intro = soup.select_one(".our-book-sec > .container > .row > .col-lg-12 p")
    if intro:
        set_text(intro, para_at(paragraphs, slots["books_intro"]))
    apply_customer_reviews_blocks(soup, parse_customer_review_testimonials(paragraphs))


def apply_faq_page(soup: BeautifulSoup, paragraphs: list[str]) -> None:
    fi = faq_start(paragraphs)
    banner_lines: list[str] = []
    i = fi + 1
    while i < len(paragraphs) and "?" not in paragraphs[i]:
        banner_lines.append(paragraphs[i])
        i += 1
    banner = soup.select_one(".about-banner .inner-heading")
    if banner and banner_lines:
        set_text(banner.select_one(".font-35"), "Our Journey")
        title = banner_lines[0]
        if title.startswith("Our Journey "):
            title = title[len("Our Journey ") :]
        set_text(banner.select_one(".main-heading"), title)
        if len(banner_lines) > 1:
            set_text(banner.select_one("p"), banner_lines[1])
    apply_faq_section(soup, paragraphs)


def replace_ubp_in_body(soup: BeautifulSoup) -> None:
    for node in soup.find_all(string=re.compile(r"United Book Publishing")):
        if node.parent and node.parent.name in {"script", "style"}:
            continue
        node.replace_with(str(node).replace("United Book Publishing", "Experts Self Publishing"))


def process_page(page: str, inventory: dict, restore: bool = False) -> None:
    path = ROOT / page
    bak = path.with_suffix(".html.bak")
    if restore and bak.exists():
        shutil.copy2(bak, path)

    html = apply_globals_raw(path.read_text(encoding="utf-8"))
    soup = BeautifulSoup(html, "html.parser")

    paragraphs: list[str] = []
    for info in inventory["sections"].values():
        if info["page"] == page:
            paragraphs = info["paragraphs"]
            break

    if paragraphs:
        apply_meta(soup, meta_title(paragraphs), first_long_para(paragraphs))

    if page == "index.html":
        apply_index_updates(soup, paragraphs)
        apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page == "book-publishing.html":
        apply_book_publishing(soup, paragraphs)
        if soup.select(".testimonial-slider"):
            apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page == "book-marketing.html":
        apply_book_marketing(soup, paragraphs)
        if soup.select(".testimonial-slider"):
            apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page in {
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
    }:
        apply_standard_service_page(soup, paragraphs, page)
        if soup.select(".testimonial-slider"):
            apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page == "pricing.html":
        apply_pricing(soup, paragraphs)
    elif page == "about-us.html":
        apply_about(soup, paragraphs)
    elif page == "published-books.html":
        apply_published_books(soup, paragraphs)
    elif page == "customer-reviews.html":
        apply_customer_reviews(soup, paragraphs)
    elif page == "faq.html":
        apply_faq_page(soup, paragraphs)

    home_paragraphs = inventory["sections"]["home"]["paragraphs"]
    apply_shared_services_section(soup, home_paragraphs)

    replace_ubp_in_body(soup)
    path.write_text(str(soup), encoding="utf-8")
    print(f"Updated {page}")


def main() -> None:
    if not INVENTORY.exists():
        raise SystemExit("Run scripts/extract_inventory.py first")
    inventory = load_inventory()
    (ROOT / "content" / "testimonials.json").write_text(
        json.dumps(TESTIMONIALS, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    import sys

    restore = "--restore" in sys.argv
    for page in CORE_PAGES:
        process_page(page, inventory, restore=restore)
    print("Apply complete.")


if __name__ == "__main__":
    main()
