"""Apply content from content/inventory.json to core HTML pages (text-only, slot-based)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from page_slots import PAGE_SLOTS


def slots_for_page(page: str, inventory: dict) -> dict:
    for info in inventory["sections"].values():
        if info["page"] == page and info.get("slots"):
            return info["slots"]
    return PAGE_SLOTS.get(page, {})

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
        if (
            p.startswith("FREQUENTLY ASKED")
            or p == "FAQ"
            or p.startswith("Frequently Asked Questions")
        ):
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


def hero_title_from_paragraph(text: str, prefix: str = "") -> str:
    if prefix and prefix in text:
        return text.split(prefix, 1)[1].strip()
    if "\n" in text:
        parts = [p.strip() for p in text.split("\n") if p.strip()]
        return parts[-1] if parts else text
    if "Professional" in text:
        return text[text.find("Professional") :].strip()
    return text.strip()


def hero_title_for_slots(paragraphs: list[str], hero: list[int], prefix: str = "") -> str:
    if len(hero) > 2:
        return para_at(paragraphs, hero[1])
    return hero_title_from_paragraph(para_at(paragraphs, hero[0]), prefix)


def cta_text_parts(paragraphs: list[str], indices: list[int]) -> list[str]:
    parts: list[str] = []
    for idx in indices:
        text = para_at(paragraphs, idx)
        if not text:
            continue
        if "\n" in text and len(parts) < 2:
            split = [p.strip() for p in text.split("\n") if p.strip()]
            parts.extend(split)
        elif not parts or parts[-1] != text:
            parts.append(text)
    return parts


def para_at(paragraphs: list[str], idx: int | str) -> str:
    if idx == "overflow":
        return ""
    if not isinstance(idx, int) or idx < 0 or idx >= len(paragraphs):
        return ""
    return paragraphs[idx]


def apply_from_slots(soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> None:
    """Map inventory paragraph indices to named HTML slots."""
    hero = slots.get("hero", [])
    if prefix := slots.get("hero_prefix_fixed"):
        intro_idx = hero[2] if len(hero) > 2 else (hero[1] if len(hero) > 1 else hero[0])
        title = hero_title_for_slots(paragraphs, hero, prefix)
        set_text(soup.select_one(".about-banner .font-35, .inner-heading .font-35"), prefix)
        set_text(soup.select_one(".main-heading, .bann-heading h1"), title)
        set_text(
            soup.select_one(".inner-heading > p, .inner-heading p.reveal, .about-banner p.reveal"),
            para_at(paragraphs, intro_idx),
        )
    elif hero:
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
            intro = box.select_one("p.para-color")
            rows = slots.get("content_rows", [])
            if intro:
                if "overflow" in rows:
                    sents = split_sentences(text)
                    set_text(intro, sents[0] if sents else text)
                    if len(sents) > 1:
                        overflow = " ".join(sents[1:])
                else:
                    set_text(intro, text)

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
            texts = cta_text_parts(paragraphs, cta_slots)
            for j, sel in enumerate(cta_sels[start:]):
                if j >= len(texts):
                    break
                el = cta.select_one(sel)
                if el:
                    set_text(el, texts[j])

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


def apply_page_our_service(soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> None:
    """Fill page-specific our-service header from image chunk (not home copy)."""
    os = slots.get("our_service")
    if not os:
        return
    svc = soup.select_one("section.our-service .our-service-hd, .our-service-hd")
    if not svc:
        return
    title = para_at(paragraphs, os["title"])
    subtitle = para_at(paragraphs, os.get("subtitle", os["title"]))
    body = para_at(paragraphs, os.get("body", os["title"]))
    top, sub = split_heading_two_line(title)
    if sub:
        set_text(svc.select_one(".font-35"), top)
        set_text(svc.select_one("h2.sec-hd"), sub)
    else:
        set_text(svc.select_one(".font-35"), title)
        set_text(svc.select_one("h2.sec-hd"), subtitle)
    intro = svc.select_one("p.para-color")
    if intro and body and body != subtitle:
        set_text(intro, body)


def apply_connect_slots(soup: BeautifulSoup, paragraphs: list[str], conn: dict) -> None:
    cta = soup.select_one(".connect-sec .cta-left")
    if not cta or not conn:
        return
    heading = para_at(paragraphs, conn["heading"])
    top, sub = split_heading_two_line(heading)
    if not sub and " Into " in heading:
        top, sub = heading.split(" Into ", 1)
        sub = f"Into {sub.strip()}"
    if not sub and " Journey " in heading:
        top, sub = heading.split(" Journey ", 1)
        sub = f"Journey {sub.strip()}"
    if not sub and " That " in heading:
        top, sub = heading.split(" That ", 1)
        sub = f"That {sub.strip()}"
    label = cta.select_one(".font-45, .font-40")
    if label:
        set_text(label, top)
    set_text(cta.select_one("h2.sec-hd"), sub or top)
    for el, idx in zip(cta.select("p"), conn.get("body", [])):
        set_text(el, para_at(paragraphs, idx))


def apply_why_choose_slots(soup: BeautifulSoup, paragraphs: list[str], wc: dict) -> None:
    choose = soup.select_one(".why-choose-sec .choose-heading")
    if not choose or not wc:
        return
    set_text(choose.select_one(".font-35"), para_at(paragraphs, wc["heading"][0]))
    set_text(choose.select_one("h2.sec-hd"), para_at(paragraphs, wc["heading"][1]))
    intro = choose.select_one("p.w-80")
    if intro:
        intro_parts = [para_at(paragraphs, i) for i in wc.get("intro", [])]
        set_text(intro, " ".join(p for p in intro_parts if p))
    for box, (ti, bi) in zip(soup.select(".why-choose-sec .choose-box"), wc.get("boxes", [])):
        set_text(box.select_one("h3"), para_at(paragraphs, ti))
        set_text(box.select_one("p"), para_at(paragraphs, bi))


def apply_process_slots(soup: BeautifulSoup, paragraphs: list[str], process: dict) -> None:
    sec = soup.select_one("section.process-tab-sec")
    if not sec or not process:
        return
    head = sec.select_one(".process-heading")
    if head:
        heading = para_at(paragraphs, process["heading"])
        top, sub = split_heading_two_line(heading)
        label = head.select_one(".font-35")
        if sub and label:
            set_text(label, top)
            set_text(head.select_one("h2.sec-hd"), sub)
        else:
            set_text(head.select_one("h2.sec-hd"), heading)
        intro = head.select_one("p")
        if intro:
            set_text(intro, para_at(paragraphs, process["intro"]))
    for box, (ti, bi) in zip(sec.select(".process-content-box"), process.get("steps", [])):
        content = box.select_one(".process-content")
        if content:
            set_text(content.select_one("h2"), para_at(paragraphs, ti))
            set_text(content.select_one("p"), para_at(paragraphs, bi))


def apply_publish_2_slots(soup: BeautifulSoup, paragraphs: list[str], p2: dict) -> None:
    sec = soup.select_one("section.publish-2")
    if not sec or not p2:
        return
    head = sec.select_one(".publish-heading")
    if head:
        set_text(head.select_one("h2.sec-hd"), para_at(paragraphs, p2["heading"]))
        intro = head.select_one("p")
        if intro:
            set_text(intro, para_at(paragraphs, p2["intro"]))
    for box, (ti, bi) in zip(sec.select(".path-box"), p2.get("paths", [])):
        h3 = box.select_one("h3")
        if h3:
            title = para_at(paragraphs, ti)
            if " " in title and "<br" not in str(h3):
                parts = title.split(" ", 1)
                set_text(h3, title)
            else:
                set_text(h3, title)
        p_el = box.select_one(".path-content p")
        if p_el:
            set_text(p_el, para_at(paragraphs, bi))


def apply_form_steps(soup: BeautifulSoup, paragraphs: list[str], form: dict) -> None:
    if not form:
        return
    for step_el, (ti, bi) in zip(soup.select(".process-step li"), form.get("steps", [])):
        title = re.sub(r"^\d+\.\s*", "", para_at(paragraphs, ti)).strip()
        set_text(step_el.select_one("h4"), title)
        set_text(step_el.select_one("p"), para_at(paragraphs, bi))


def apply_standard_service_page(soup: BeautifulSoup, paragraphs: list[str], page: str, inventory: dict) -> None:
    """Fill the shared service-page template from slot manifest."""
    slots = slots_for_page(page, inventory)
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


def apply_book_publishing(soup: BeautifulSoup, paragraphs: list[str], slots: dict | None = None) -> None:
    slots = slots or PAGE_SLOTS.get("book-publishing.html", {})

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
        closing = sk.get("closing", [])
        if closing:
            p_el = self_sec.select_one(".col-lg-6 p.text-white")
            if p_el:
                set_text(p_el, para_at(paragraphs, closing[0]))
            if len(closing) > 1:
                h5 = self_sec.select_one(".col-lg-6 h5.color")
                if h5:
                    set_text(h5, para_at(paragraphs, closing[1]))

    p1 = slots.get("publish_1")
    pub = soup.select_one("section.publish-1 .publish-heading")
    if pub and p1:
        set_text(pub.select_one("h2.sec-hd"), para_at(paragraphs, p1["heading"]))
        for el, idx in zip(pub.select("p")[:2], p1["body"]):
            set_text(el, para_at(paragraphs, idx))

    testi = soup.select_one(".testi-heading")
    if testi and (ti := slots.get("testi")):
        set_text(testi.select_one(".font-35"), para_at(paragraphs, ti[0]))
        set_text(testi.select_one(".sec-hd"), para_at(paragraphs, ti[1]))
        set_text(testi.select_one("p"), para_at(paragraphs, ti[2]))

    apply_process_slots(soup, paragraphs, slots.get("process", {}))
    apply_connect_slots(soup, paragraphs, slots.get("connect", {}))
    apply_why_choose_slots(soup, paragraphs, slots.get("why_choose", {}))
    apply_publish_2_slots(soup, paragraphs, slots.get("publish_2", {}))

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


def apply_index_updates(soup: BeautifulSoup, paragraphs: list[str], slots: dict) -> None:
    for sel, idx in zip(
        (".bann-heading h1.first-content", ".bann-heading h2.bann-hd", ".bann-heading .main-para"),
        slots.get("hero", [0, 1, 2]),
    ):
        set_text(soup.select_one(sel), para_at(paragraphs, idx))

    pub = soup.select_one(".publish-sec .s1-left")
    ps = slots.get("publish_sec", {})
    if pub and ps:
        heading = para_at(paragraphs, ps.get("heading", 3))
        if "Self-Publishing Partner" in heading:
            set_text(pub.select_one(".font-35"), heading.split("Self-Publishing")[0].strip())
            set_text(pub.select_one("h2.sec-hd"), "Self-Publishing Partner?")
        else:
            top, sub = split_heading_two_line(heading)
            set_text(pub.select_one(".font-35"), top)
            set_text(pub.select_one("h2.sec-hd"), sub or heading)
        for el, idx in zip(pub.select("p.reveal"), ps.get("body", [4, 5])):
            set_text(el, para_at(paragraphs, idx))

    svc = soup.select_one(".our-service-hd")
    si = slots.get("services_intro", [8, 9, 10])
    if svc and isinstance(si, list) and len(si) >= 3:
        set_text(svc.select_one(".font-35"), para_at(paragraphs, si[0]))
        set_text(svc.select_one("h2.sec-hd"), para_at(paragraphs, si[1]))
        set_text(svc.select_one("p.para-color"), para_at(paragraphs, si[2]))

    ti = slots.get("testi_intro", [11, 12, 13])
    if isinstance(ti, list) and len(ti) >= 3:
        set_text(soup.select_one(".testi-heading .font-35"), para_at(paragraphs, ti[0]))
        sub_text = para_at(paragraphs, ti[1])
        body_text = para_at(paragraphs, ti[2])
        if ". At Experts" in sub_text:
            h2, tail = sub_text.split(". At Experts", 1)
            sub_text = h2.strip() + "."
            body_text = f"At Experts{tail} {body_text}".strip()
        set_text(soup.select_one(".testi-heading .sec-hd"), sub_text)
        intro = soup.select_one(".testi-heading p.w-80")
        if intro:
            set_text(intro, body_text)

    cta = soup.select_one(".connect-sec .cta-left")
    conn = slots.get("connect", {})
    if cta and conn:
        set_text(cta.select_one(".font-45"), conn.get("fixed_h3", "Your Trusted"))
        set_text(cta.select_one("h2.sec-hd"), conn.get("fixed_h2", "Self-Publishing Experts"))
        for el, idx in zip(cta.select("p"), conn.get("body", [15, 16])):
            set_text(el, para_at(paragraphs, idx))

    choose = soup.select_one(".why-choose-sec .choose-heading")
    wc = slots.get("why_choose", {})
    if choose and wc:
        set_text(choose.select_one(".font-35"), para_at(paragraphs, wc["heading"][0]))
        set_text(choose.select_one("h2.sec-hd"), para_at(paragraphs, wc["heading"][1]))
        intro = choose.select_one("p.w-80")
        if intro:
            intro_parts = wc.get("intro", [])
            if isinstance(intro_parts, list):
                text = " ".join(para_at(paragraphs, i) for i in intro_parts if isinstance(i, int))
            else:
                text = para_at(paragraphs, intro_parts)
            set_text(intro, text)
    for box, (ti, bi) in zip(soup.select(".why-choose-sec .choose-box"), wc.get("boxes", [])):
        set_text(box.select_one("h3"), para_at(paragraphs, ti))
        set_text(box.select_one("p"), para_at(paragraphs, bi))

    apply_form_steps(soup, paragraphs, slots.get("form", {}))


def apply_book_marketing(soup: BeautifulSoup, paragraphs: list[str], slots: dict | None = None) -> None:
    slots = slots or {}

    banner = slots.get("banner", {})
    h1 = soup.select_one(".inner-banner .bann-heading h1")
    sub = soup.select_one(".inner-banner .bann-heading > p.text-white")
    if h1 and banner.get("h1"):
        h1_parts = banner["h1"]
        if isinstance(h1_parts, list):
            set_text(h1, " ".join(para_at(paragraphs, i) for i in h1_parts))
        else:
            set_text(h1, para_at(paragraphs, h1_parts))
    if sub and "intro" in banner:
        set_text(sub, para_at(paragraphs, banner["intro"]))
    for box, (title_i, body_i) in zip(soup.select(".inner-banner .bann-box"), banner.get("boxes", [])):
        h4 = box.select_one("h4")
        p = box.select_one(".box-content p")
        if h4:
            set_text(h4, para_at(paragraphs, title_i))
        if p:
            set_text(p, para_at(paragraphs, body_i))

    s1 = soup.select_one(".marketing-sec .s1-left")
    if s1 and slots.get("s1"):
        s1s = slots["s1"]
        set_text(s1.select_one(".font-35"), para_at(paragraphs, s1s["heading"][0]))
        set_text(s1.select_one("h2.sec-hd"), para_at(paragraphs, s1s["heading"][1]))
        for el in s1.select("p"):
            set_text(el, "")

    cta_sec = soup.select_one("section.cta-sec .cta-content")
    if cta_sec and slots.get("cta"):
        cta = slots["cta"]
        set_text(cta_sec.select_one("h3.bg-rect"), para_at(paragraphs, cta["h3"]))
        set_text(cta_sec.select_one("h2.sec-hd"), para_at(paragraphs, cta["h2"]))
        body_parts = [para_at(paragraphs, i) for i in cta.get("body", [])]
        intro = cta_sec.select_one("p")
        if intro and body_parts:
            set_text(intro, " ".join(p for p in body_parts if p))

    service = soup.select_one("section.inner-service .service-heading")
    if service and slots.get("inner_service"):
        ins = slots["inner_service"]
        set_text(service.select_one("h2.sec-hd"), para_at(paragraphs, ins["heading"]))
        intro = service.select_one("p")
        if intro:
            set_text(intro, para_at(paragraphs, ins["intro"]))

    for box, (title_i, body_i) in zip(soup.select("section.inner-service .market-box"), slots.get("market_boxes", [])):
        h3 = box.select_one("h3")
        p = box.select_one(".market-content p")
        if h3:
            set_text(h3, para_at(paragraphs, title_i))
        if p:
            set_text(p, para_at(paragraphs, body_i))

    process = soup.select_one("section.process-tab-sec .process-heading")
    if process and slots.get("process"):
        proc = slots["process"]
        heading = para_at(paragraphs, proc["heading"])
        top, sub = split_heading_two_line(heading)
        if sub:
            set_text(process.select_one(".font-35"), top)
            set_text(process.select_one("h2.sec-hd"), sub)
        else:
            set_text(process.select_one(".font-35"), "")
            set_text(process.select_one("h2.sec-hd"), heading)
        intro = process.select_one("p")
        if intro:
            set_text(intro, para_at(paragraphs, proc["intro"]))

    testi = soup.select_one(".testi-heading")
    if testi and slots.get("testi"):
        ti = slots["testi"]
        set_text(testi.select_one(".font-35"), para_at(paragraphs, ti[0]))
        set_text(testi.select_one(".sec-hd"), para_at(paragraphs, ti[1]))
        intro = testi.select_one("p")
        if intro and len(ti) > 2:
            set_text(intro, para_at(paragraphs, ti[2]))

    apply_why_choose_slots(soup, paragraphs, slots.get("why_choose", {}))
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


def apply_about(soup: BeautifulSoup, paragraphs: list[str], slots: dict | None = None) -> None:
    slots = slots or PAGE_SLOTS.get("about-us.html", {})
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

    apply_connect_slots(soup, paragraphs, slots.get("connect", {}))
    apply_form_steps(soup, paragraphs, slots.get("form", {}))


def apply_published_books(soup: BeautifulSoup, paragraphs: list[str], slots: dict | None = None) -> None:
    slots = slots or PAGE_SLOTS.get("published-books.html", {})
    for sel, idx in zip((".font-35", ".main-heading", "p.reveal, p"), slots["banner"]):
        el = soup.select_one(f".inner-heading {sel}, .about-banner {sel}")
        if el:
            set_text(el, para_at(paragraphs, idx))
    pub = slots.get("publish_sec")
    if pub:
        head = soup.select_one(".publish-book .publish-heading")
        if head:
            set_text(head.select_one("h2.sec-hd"), para_at(paragraphs, pub["heading"]))
            intro = head.select_one("p.para-color")
            if intro:
                set_text(intro, para_at(paragraphs, pub["intro"]))
    apply_form_steps(soup, paragraphs, slots.get("form", {}))


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


def apply_customer_reviews(soup: BeautifulSoup, paragraphs: list[str], slots: dict | None = None) -> None:
    slots = slots or PAGE_SLOTS.get("customer-reviews.html", {})
    for sel, idx in zip((".font-35", ".main-heading", "p"), slots["banner"]):
        el = soup.select_one(f".inner-heading {sel}")
        if el:
            set_text(el, para_at(paragraphs, idx))
    if "testi_heading" in slots:
        set_text(soup.select_one(".our-book-sec .sec-hd"), para_at(paragraphs, slots["testi_heading"]))
        intro = soup.select_one(".our-book-sec > .container > .row > .col-lg-12 p")
        if intro:
            set_text(intro, para_at(paragraphs, slots["testi_intro"]))
    apply_customer_reviews_blocks(soup, parse_customer_review_testimonials(paragraphs))
    apply_connect_slots(soup, paragraphs, slots.get("connect", {}))
    apply_why_choose_slots(soup, paragraphs, slots.get("why_choose", {}))
    apply_form_steps(soup, paragraphs, slots.get("form", {}))


def apply_faq_page(soup: BeautifulSoup, paragraphs: list[str], slots: dict | None = None) -> None:
    slots = slots or {}
    fi = faq_start(paragraphs)
    banner_lines: list[str] = []
    i = fi + 1
    while i < len(paragraphs) and "?" not in paragraphs[i]:
        banner_lines.append(paragraphs[i])
        i += 1
    banner = soup.select_one(".about-banner .inner-heading")
    if banner and banner_lines:
        set_text(banner.select_one(".font-35"), slots.get("banner_fixed_label", "Our Journey"))
        title = banner_lines[0]
        if title.startswith("Our Journey "):
            title = title[len("Our Journey ") :]
        set_text(banner.select_one(".main-heading"), title)
        if len(banner_lines) > 1:
            set_text(banner.select_one("p"), banner_lines[1])
    apply_faq_section(soup, paragraphs)
    apply_connect_slots(soup, paragraphs, slots.get("connect", {}))
    apply_why_choose_slots(soup, paragraphs, slots.get("why_choose", {}))
    apply_form_steps(soup, paragraphs, slots.get("form", {}))


def replace_ubp_in_body(soup: BeautifulSoup) -> None:
    for node in soup.find_all(string=re.compile(r"Experts Self Publishing")):
        if node.parent and node.parent.name in {"script", "style"}:
            continue
        node.replace_with(str(node).replace("Experts Self Publishing", "Experts Self Publishing"))


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

    page_slots = slots_for_page(page, inventory)

    if page == "index.html":
        apply_index_updates(soup, paragraphs, page_slots)
        apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page == "book-publishing.html":
        apply_book_publishing(soup, paragraphs, page_slots)
        if soup.select(".testimonial-slider"):
            apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page == "book-marketing.html":
        apply_book_marketing(soup, paragraphs, page_slots)
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
        apply_standard_service_page(soup, paragraphs, page, inventory)
        if soup.select(".testimonial-slider"):
            apply_testimonial_boxes(soup, TESTIMONIALS)
    elif page == "pricing.html":
        apply_pricing(soup, paragraphs)
    elif page == "about-us.html":
        apply_about(soup, paragraphs, page_slots)
    elif page == "published-books.html":
        apply_published_books(soup, paragraphs, page_slots)
    elif page == "customer-reviews.html":
        apply_customer_reviews(soup, paragraphs, page_slots)
    elif page == "faq.html":
        apply_faq_page(soup, paragraphs, page_slots)

    if page_slots.get("our_service"):
        apply_page_our_service(soup, paragraphs, page_slots)
    elif page != "index.html":
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
