"""Infer PAGE_SLOTS indices from image-delimited text chunks."""
from __future__ import annotations

import re

HERO_PREFIX_PAGES = {
    "ghostwriting.html": "Tell Your Story With",
    "book-video-trailers.html": "Promote Your Book With",
}

HEADING_EMPTY_PAGES = {
    "ghostwriting.html",
    "book-video-trailers.html",
    "creative-writing.html",
    "children-book-illustration.html",
    "screenplay-script-writing.html",
}

CTA_MARKERS = (
    "From First Draft",
    "From Manuscript",
    "From Draft",
    "From Simple",
    "From Concept",
    "From Story to",
    "Turn Your Manuscript",
    "From Manuscript to Online",
)


def is_short_heading(text: str) -> bool:
    return len(text) < 75 and not text.endswith(".") and "?" not in text


def chunk_start_indices(chunks: list[list[str]]) -> tuple[list[str], list[int]]:
    flat: list[str] = []
    starts: list[int] = []
    for chunk in chunks:
        starts.append(len(flat))
        flat.extend(chunk)
    return flat, starts


def is_cta_chunk(chunk: list[str]) -> bool:
    if not chunk:
        return False
    head = chunk[0]
    if any(m in head for m in CTA_MARKERS):
        return True
    if len(chunk) >= 2 and any(
        x in chunk[1] for x in ("Let Your Story Reach", "Bring Your Book", "Bring Your Story")
    ):
        return True
    if len(chunk) <= 3 and all(len(line) < 120 for line in chunk):
        joined = " ".join(chunk[:2]).lower()
        if "published" in joined and ("success" in joined or "readers" in joined):
            return True
    return False


def is_faq_intro_chunk(chunk: list[str]) -> bool:
    if not chunk:
        return False
    head = chunk[0]
    head_lower = head.lower()
    return (
        head.startswith("FREQUENTLY")
        or head.startswith("Frequently Asked")
        or head_lower.startswith("answers with")
        or head.startswith("Common Questions")
        or "Questions About" in " ".join(chunk[:2])
        or head.startswith("Answers With")
    )


def faq_paragraph_index(paragraphs: list[str]) -> int:
    for i, p in enumerate(paragraphs):
        if is_faq_intro_chunk([p]):
            return i
    return len(paragraphs)


def infer_why_choose_chunk(flat: list[str], s0: int, s1: int) -> dict:
    start = s0
    if start < s1 and flat[start].endswith(".") and not is_short_heading(flat[start]):
        start += 1
    intro_idx = start + 2
    if intro_idx < s1 and not is_short_heading(flat[intro_idx]):
        intro = [intro_idx]
        box_start = intro_idx + 1
    else:
        intro = [start + 2, start + 3] if start + 3 < s1 else [start + 2]
        box_start = start + 4 if start + 4 < s1 else start + 2
    boxes: list[tuple[int, int]] = []
    i = box_start
    while i + 1 < s1 and len(boxes) < 4:
        if is_short_heading(flat[i]) and flat[i + 1].endswith("."):
            boxes.append((i, i + 1))
            i += 2
        else:
            i += 1
    return {
        "heading": [start, start + 1],
        "intro": intro,
        "boxes": boxes,
    }


def infer_connect_chunk(flat: list[str], s0: int, s1: int) -> dict:
    body = [i for i in range(s0 + 1, min(s0 + 3, s1)) if flat[i].endswith(".")]
    return {"heading": s0, "body": body or list(range(s0 + 1, min(s0 + 3, s1)))}


def infer_form_steps(flat: list[str], s0: int, s1: int) -> list[tuple[int, int]]:
    """Sidebar process steps; chunk may start with '01' + title or 'Get Started' label + intro."""
    steps: list[tuple[int, int]] = []
    i = s0
    if i < s1 and flat[i] == "Get Started" and i + 1 < s1:
        steps.append((i, i + 1))
        i += 2
    elif i < s1 and re.fullmatch(r"\d{1,2}", flat[i]) and i + 2 < s1:
        steps.append((i + 1, i + 2))
        i += 3
    else:
        i = s0 + 2
    while i + 1 < s1:
        if re.fullmatch(r"\d{1,2}", flat[i]) and i + 2 < s1:
            steps.append((i + 1, i + 2))
            i += 3
        elif is_short_heading(flat[i]) and flat[i + 1].endswith("."):
            steps.append((i, i + 1))
            i += 2
        else:
            i += 1
    return steps


def infer_publish_paths(flat: list[str], s0: int, s1: int) -> dict:
    paths: list[tuple[int, int]] = []
    i = s0 + 2
    while i + 1 < s1 and len(paths) < 3:
        if is_short_heading(flat[i]):
            paths.append((i, i + 1))
            i += 2
        else:
            i += 1
    return {"heading": s0, "intro": s0 + 1, "paths": paths}


def is_our_service_chunk(chunk: list[str]) -> bool:
    if not chunk:
        return False
    head = chunk[0]
    return any(
        x in head
        for x in (
            "Your Vision",
            "Your Ambition",
            "Complete Publishing",
            "Complete Self Publishing",
            "Your Publishing Goals",
        )
    )


def classify_middle_chunks(chunks: list[list[str]]) -> dict[str, int]:
    """Map chunk role -> chunk index for slots between about and FAQ."""
    roles: dict[str, int] = {}
    for i in range(2, len(chunks)):
        chunk = chunks[i]
        if is_faq_intro_chunk(chunk):
            roles["faq_intro"] = i
            break
        if is_our_service_chunk(chunk):
            roles.setdefault("our_service", i)
            continue
        if is_cta_chunk(chunk):
            roles.setdefault("cta", i)
            continue
        roles.setdefault("make", i)
    if "cta" not in roles and len(chunks) > 2:
        roles["cta"] = 2
    if "make" not in roles and len(chunks) > 3:
        for i in range(2, len(chunks)):
            if i != roles.get("cta") and i != roles.get("our_service"):
                roles["make"] = i
                break
    if "our_service" not in roles:
        for i in range(2, len(chunks)):
            if i not in {roles.get("cta"), roles.get("make"), roles.get("faq_intro")}:
                if is_our_service_chunk(chunks[i]):
                    roles["our_service"] = i
                    break
        if "our_service" not in roles and len(chunks) > 4:
            candidate = roles.get("faq_intro", len(chunks)) - 1
            if candidate > roles.get("make", 2):
                roles["our_service"] = candidate
    return roles


def body_rows(intro_idx: int, chunk_end: int) -> list:
    """All paragraph indices after intro within a chunk (with overflow for intro remainder)."""
    if intro_idx + 1 >= chunk_end:
        return ["overflow"]
    return ["overflow"] + list(range(intro_idx + 1, chunk_end))


def infer_standard_service_slots(page: str, chunks: list[list[str]]) -> dict:
    if len(chunks) < 3:
        return {}

    flat, starts = chunk_start_indices(chunks)

    def end(i: int) -> int:
        return starts[i + 1] if i + 1 < len(starts) else len(flat)

    slots: dict = {}

    # --- Hero (chunk 0) ---
    h0, h1 = starts[0], end(0)
    if page in HERO_PREFIX_PAGES:
        slots["hero_prefix_fixed"] = HERO_PREFIX_PAGES[page]
        intro_i = h0 + 2 if h1 - h0 >= 3 else (h0 + 1 if h1 - h0 >= 2 else h0)
        slots["hero"] = [h0, h0 + 1, intro_i]
    elif h1 - h0 >= 3:
        slots["hero"] = [h0, h0 + 1, h0 + 2]
    elif h1 - h0 == 2:
        slots["hero"] = [h0, h0 + 1, h0 + 1]
    else:
        slots["hero"] = [h0, h0, h0]

    # --- About (chunk 1) ---
    a0, a1 = starts[1], end(1)
    if (
        a1 - a0 >= 2
        and is_short_heading(flat[a0])
        and is_short_heading(flat[a0 + 1])
    ):
        slots["content_heading_split"] = [a0, a0 + 1]
        intro_i = a0 + 2
        slots["content_intro"] = intro_i
        slots["content_rows"] = list(range(intro_i + 1, a1)) if a1 > intro_i + 1 else []
    elif page in HEADING_EMPTY_PAGES:
        if is_short_heading(flat[a0]) and a0 + 1 < a1 and flat[a0 + 1].endswith("."):
            slots["content_heading"] = a0
            slots["content_intro"] = a0 + 1
            slots["content_rows"] = list(range(a0 + 2, a1)) if a0 + 2 < a1 else []
        else:
            slots["content_heading_empty"] = True
            slots["content_intro"] = a0
            slots["content_rows"] = body_rows(a0, a1) if a1 > a0 else ["overflow"]
    elif a1 - a0 >= 2 and is_short_heading(flat[a0]) and not flat[a0 + 1].endswith("."):
        slots["content_heading"] = a0
        intro_i = a0 + 1
        slots["content_intro"] = intro_i
        slots["content_rows"] = body_rows(intro_i, a1) if a1 > intro_i else []
    else:
        slots["content_heading"] = a0
        intro_i = a0 + 1 if a1 > a0 + 1 else a0
        slots["content_intro"] = intro_i
        slots["content_rows"] = body_rows(intro_i, a1) if a1 > intro_i else []

    # --- Middle chunks: make / CTA / our-service (role detection, not fixed offsets) ---
    roles = classify_middle_chunks(chunks)

    if cta_i := roles.get("cta"):
        c0, c1 = starts[cta_i], end(cta_i)
        if c1 - c0 >= 3:
            slots["cta"] = [c0, c0 + 1, c0 + 2]
        elif c1 - c0 == 2:
            slots["cta"] = [c0, c0 + 1, c0 + 1]
        elif c1 - c0 == 1:
            slots["cta"] = [c0, c0, c0]
        else:
            slots["cta_no_doc"] = True
    else:
        slots["cta_no_doc"] = True

    if make_i := roles.get("make"):
        m0, m1 = starts[make_i], end(make_i)
        slots["make_title"] = m0
        slots["make_body"] = list(range(m0 + 1, m1))

    if os_i := roles.get("our_service"):
        b0, b1 = starts[os_i], end(os_i)
        slots["our_service"] = {
            "title": b0,
            "subtitle": b0 + 1 if b1 > b0 + 1 else b0,
            "body": b0 + 2 if b1 > b0 + 2 else (b0 + 1 if b1 > b0 + 1 else b0),
        }

    return slots


def infer_process_steps_chunk(flat: list[str], s0: int, s1: int) -> list[tuple[int, int]]:
    """Numbered sidebar steps (01. Get Started, etc.) within a chunk."""
    steps: list[tuple[int, int]] = []
    i = s0
    while i + 1 < s1:
        if is_short_heading(flat[i]) and flat[i + 1].endswith("."):
            steps.append((i, i + 1))
            i += 2
        else:
            i += 1
    return steps


def infer_index_slots(chunks: list[list[str]]) -> dict:
    flat, starts = chunk_start_indices(chunks)
    if len(starts) < 6:
        return {"type": "index", "hero": [0, 1, 2]}

    def end(i: int) -> int:
        return starts[i + 1] if i + 1 < len(starts) else len(flat)

    s1, s2, s3, s4, s5 = starts[1], starts[2], starts[3], starts[4], starts[5]
    wc_end = end(5)

    pub_heading = s1
    pub_body: list[int] = []
    chunk1_end = s2
    for i in range(s1, chunk1_end):
        line = flat[i]
        if "Self-Publishing Partner" in line or "Self-publishing Partner" in line:
            pub_heading = i
            pub_body = [j for j in range(i + 1, chunk1_end) if flat[j].endswith(".")]
            break
    if len(pub_body) < 2:
        pub_body = [j for j in range(pub_heading + 1, chunk1_end) if flat[j].endswith(".")][:2]

    boxes: list[tuple[int, int]] = []
    i = s5 + 3
    while i + 1 < wc_end and len(boxes) < 4:
        if is_short_heading(flat[i]) and flat[i + 1].endswith("."):
            boxes.append((i, i + 1))
            i += 2
        else:
            i += 1

    connect_body = [s4 + 1, s4 + 2]
    if flat[s4].startswith("Your Trusted"):
        connect_body = [s4 + 1, s4 + 2]
    elif s4 + 2 < len(flat):
        connect_body = [s4, s4 + 1]

    testi_end = s4 if s4 > s3 else starts[4] if len(starts) > 4 else s3 + 4
    testi_lines = list(range(s3, testi_end))
    testi_label = testi_lines[0] if testi_lines else s3
    testi_sub = testi_lines[1] if len(testi_lines) > 1 else s3 + 1
    testi_body = testi_lines[2] if len(testi_lines) > 2 else s3 + 2
    for idx in testi_lines[2:]:
        if len(flat[idx]) > len(flat[testi_body]):
            testi_body = idx

    slots: dict = {
        "type": "index",
        "hero": [0, 1, 2],
        "publish_sec": {"heading": pub_heading, "body": pub_body},
        "services_intro": [s2, s2 + 1, s2 + 2],
        "testi_intro": [testi_label, testi_sub, testi_body],
        "connect": {
            "fixed_h3": "Your Trusted",
            "fixed_h2": "Self-Publishing Experts",
            "body": connect_body,
        },
        "why_choose": {
            "heading": [s5, s5 + 1],
            "intro": [s5 + 2],
            "boxes": boxes,
        },
    }
    if len(starts) > 6:
        steps = infer_process_steps_chunk(flat, starts[6], end(6))
        if steps:
            slots["form"] = {"steps": steps}
    return slots


def infer_book_publishing_slots(chunks: list[list[str]]) -> dict:
    flat, starts = chunk_start_indices(chunks)

    def end(i: int) -> int:
        return starts[i + 1] if i + 1 < len(starts) else len(flat)

    slots: dict = {
        "type": "book_publishing",
        "cta_h3_fixed": "Your Next Chapter Starts Here",
        "banner": [starts[0], starts[0] + 1] if starts else [0, 1],
        "s1_heading": starts[1] if len(starts) > 1 else 2,
        "s1_body": list(range(starts[1] + 1, end(1))) if len(starts) > 1 else [3, 4, 5],
    }

    roles = classify_middle_chunks(chunks)
    if cta_i := roles.get("cta"):
        c0 = starts[cta_i]
        slots["cta"] = [c0, c0 + 1] if end(cta_i) > c0 + 1 else [c0, c0]
    elif len(starts) > 2:
        slots["cta"] = [starts[2], starts[2] + 1]

    if len(starts) > 3:
        k0, k1 = starts[3], end(3)
        bullets = [i for i in range(k0 + 3, k1) if len(flat[i]) < 120 and not flat[i].endswith(".")]
        if len(bullets) < 4:
            bullets = list(range(k0 + 3, min(k0 + 7, k1)))
        closing_start = bullets[-1] + 1 if bullets else k0 + 3
        slots["kdp"] = {
            "heading": k0,
            "intro": [k0 + 1, k0 + 2],
            "bullets": bullets[:4],
            "closing": [closing_start, closing_start + 1] if closing_start + 1 < k1 else [closing_start],
        }

    if len(starts) > 4:
        s0, s1 = starts[4], end(4)
        benefits = []
        i = s0 + 2
        while i + 1 < s1 and len(benefits) < 5:
            if is_short_heading(flat[i]):
                benefits.append((i, i + 1))
                i += 2
            else:
                i += 1
        last_used = benefits[-1][1] if benefits else s0 + 1
        closing = list(range(last_used + 1, s1))
        slots["self_kdp"] = {
            "heading": s0,
            "intro": s0 + 1,
            "benefits": benefits or [(s0 + 2, s0 + 3)],
            "closing": closing[:2] if closing else [],
        }

    for i, start in enumerate(starts):
        if i < 5:
            continue
        chunk = chunks[i]
        if not chunk:
            continue
        s1 = end(i)
        if "Publish Your Book on the Right Platforms" in chunk[0]:
            slots["publish_1"] = {"heading": start, "body": [start + 1, start + 2]}
        elif chunk[0].startswith("Trusted by Authors"):
            third = start + 2 if start + 2 < s1 else start + 1
            slots["testi"] = [start, start + 1, third]
        elif "Step-by-Step Publishing Process" in chunk[0] or chunk[0].startswith("A Clear,"):
            steps: list[tuple[int, int]] = []
            j = start + 2
            while j + 1 < s1:
                if is_short_heading(flat[j]):
                    steps.append((j, j + 1))
                    j += 2
                else:
                    j += 1
            slots["process"] = {
                "heading": start,
                "intro": start + 1,
                "steps": steps[:1] or [(start + 2, start + 3)],
            }
        elif chunk[0].startswith("Ready to Turn Your Book"):
            slots["connect"] = infer_connect_chunk(flat, start, s1)
        elif chunk[0].startswith("More Than a"):
            slots["why_choose"] = infer_why_choose_chunk(flat, start, s1)
        elif chunk[0].startswith("Find the Best Way"):
            slots["publish_2"] = infer_publish_paths(flat, start, s1)

    return slots


def infer_pricing_slots(chunks: list[list[str]]) -> dict:
    flat = [p for ch in chunks for p in ch]
    if not flat:
        return {"type": "pricing", "cta_no_doc": True}
    merged = flat[0]
    if len(flat) == 1 and "Packages" in merged:
        match = re.match(r"(.+?)\s+Packages\s+(.+)", merged)
        if match:
            return {
                "type": "pricing",
                "banner": [0, 0, 1] if len(flat) > 1 else [0, 0, 0],
                "cta_no_doc": True,
            }
    return {
        "type": "pricing",
        "banner": [0, 1, 2] if len(flat) >= 3 else list(range(len(flat))),
        "cta_no_doc": True,
    }


def infer_about_slots(chunks: list[list[str]]) -> dict:
    flat, starts = chunk_start_indices(chunks)
    if len(chunks) < 3:
        return {}

    def end(i: int) -> int:
        return starts[i + 1] if i + 1 < len(starts) else len(flat)

    b1 = starts[1]
    c2 = starts[2]
    slots: dict = {
        "banner_fixed_label": "Our Journey",
        "banner": [b1, b1 + 1],
        "about_heading": b1 + 2,
        "about_intro": b1 + 3,
        "about_rows": list(range(b1 + 4, c2)) or [b1 + 4],
        "cta": [c2, c2 + 1, c2 + 2],
    }

    if len(starts) > 3:
        os0 = starts[3]
        slots["our_service"] = {
            "title": os0,
            "subtitle": os0 + 1,
            "body": os0 + 2,
        }
    if len(starts) > 4:
        slots["connect"] = infer_connect_chunk(flat, starts[4], end(4))
    if len(starts) > 5:
        gs0 = starts[5]
        slots["form"] = {
            "heading": gs0,
            "intro": gs0 + 1,
            "steps": infer_form_steps(flat, gs0, end(5)),
        }
    return slots


def infer_market_boxes(flat: list[str], s0: int, s1: int) -> list[tuple[int, int]]:
    """Short title + long body pairs (HTML shows body in h3, title in p)."""
    boxes: list[tuple[int, int]] = []
    i = s0
    while i + 1 < s1:
        if is_short_heading(flat[i]) or (len(flat[i]) < 90 and not flat[i].endswith(".")):
            boxes.append((i, i + 1))
            i += 2
        else:
            i += 1
    return boxes


def infer_book_marketing_slots(chunks: list[list[str]]) -> dict:
    flat, starts = chunk_start_indices(chunks)

    def end(i: int) -> int:
        return starts[i + 1] if i + 1 < len(starts) else len(flat)

    c0 = starts[0] if starts else 0
    slots: dict = {
        "type": "book_marketing",
        "banner": {
            "h1": c0,
            "subtitle": c0 + 1,
            "boxes": [(c0 + 2, c0 + 3), (c0 + 4, c0 + 5), (c0 + 6, c0 + 7)],
            "tagline": c0 + 8,
        },
    }
    if len(starts) > 1:
        s = starts[1]
        e1 = end(1)
        body = [s + 4]
        if s + 5 < e1:
            body.append(s + 5)
        slots["s1"] = {"heading": [s, s + 1], "tagline": c0 + 8}
        slots["cta"] = {"h3": s + 2, "h2": s + 3, "body": body}
    if len(starts) > 2:
        s = starts[2]
        slots["inner_service"] = {"heading": s, "intro": s + 1}
    if len(starts) > 3:
        s = starts[3]
        slots["market_boxes"] = infer_market_boxes(flat, s, end(3))
    if len(starts) > 4:
        s = starts[4]
        slots["process"] = {"heading": s, "intro": s + 1}
    if len(starts) > 5:
        s = starts[5]
        slots["testi"] = [s, s + 1, s + 2]
    if len(starts) > 6:
        s = starts[6]
        slots["why_choose"] = infer_why_choose_chunk(flat, s, end(6))
    return slots


def infer_simple_banner_slots(page: str, chunks: list[list[str]]) -> dict:
    flat, starts = chunk_start_indices(chunks)

    def end(i: int) -> int:
        return starts[i + 1] if i + 1 < len(starts) else len(flat)

    if page == "published-books.html":
        c0 = starts[0] if starts else 0
        slots: dict = {"banner": [c0, c0 + 1, c0 + 2]} if len(flat) >= c0 + 3 else {"banner": list(range(len(flat)))}
        if len(starts) > 1:
            p0 = starts[1]
            slots["publish_sec"] = {"heading": p0, "intro": p0 + 1}
        if len(starts) > 2:
            gs0 = starts[2]
            slots["form"] = {
                "heading": gs0,
                "intro": gs0 + 1,
                "steps": infer_form_steps(flat, gs0, end(2)),
            }
        return slots
    if page == "customer-reviews.html":
        c0 = starts[0] if starts else 0
        slots = {
            "banner": [c0, c0 + 1, c0 + 2],
            "testi_heading": starts[1] if len(starts) > 1 else c0 + 3,
            "testi_intro": starts[1] + 1 if len(starts) > 1 else c0 + 4,
        }
        connect_at = None
        why_at = None
        form_at = len(flat)
        for i, start in enumerate(starts):
            chunk = chunks[i]
            if not chunk:
                continue
            s1 = end(i)
            if connect_at is None:
                connect_at = next(
                    (start + j for j, line in enumerate(chunk) if line.startswith("Start Your Publishing Journey")),
                    None,
                )
            if why_at is None:
                why_at = next(
                    (start + j for j, line in enumerate(chunk) if line.startswith("More Than a")),
                    None,
                )
            if chunk[0] == "Get Started":
                form_at = start
                if "form" not in slots:
                    slots["form"] = {
                        "heading": start,
                        "intro": start + 1,
                        "steps": infer_form_steps(flat, start, s1),
                    }
        if connect_at is not None:
            conn_end = why_at if why_at and why_at > connect_at else form_at
            slots["connect"] = infer_connect_chunk(flat, connect_at, conn_end)
        if why_at is not None:
            slots["why_choose"] = infer_why_choose_chunk(flat, why_at, form_at)
        return slots
    if page == "faq.html":
        flat, starts = chunk_start_indices(chunks)

        def end(i: int) -> int:
            return starts[i + 1] if i + 1 < len(starts) else len(flat)

        slots: dict = {"type": "faq", "banner_fixed_label": "Our Journey"}
        if len(starts) > 2:
            connect_at = starts[2]
            slots["connect"] = infer_connect_chunk(flat, connect_at, end(2))
        if len(starts) > 3:
            why_at = starts[3]
            form_at = starts[4] if len(starts) > 4 else len(flat)
            slots["why_choose"] = infer_why_choose_chunk(flat, why_at, form_at)
        if len(starts) > 4:
            gs0 = starts[4]
            slots["form"] = {
                "heading": gs0,
                "intro": gs0 + 1,
                "steps": infer_form_steps(flat, gs0, end(4)),
            }
        return slots
    return {}


def infer_slots(page: str, chunks: list[list[str]]) -> dict:
    if page == "index.html":
        return infer_index_slots(chunks)
    if page == "book-publishing.html":
        return infer_book_publishing_slots(chunks)
    if page == "book-marketing.html":
        return infer_book_marketing_slots(chunks)
    if page == "pricing.html":
        return infer_pricing_slots(chunks)
    if page == "about-us.html":
        return infer_about_slots(chunks)
    if page in {"published-books.html", "customer-reviews.html", "faq.html"}:
        return infer_simple_banner_slots(page, chunks)
    return infer_standard_service_slots(page, chunks)
