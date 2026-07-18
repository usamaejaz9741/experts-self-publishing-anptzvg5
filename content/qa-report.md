# Sitewide Content Migration — QA Report

**Date:** 2026-07-17  
**Scope:** 18 core marketing HTML pages

## Content pipeline (use after every docx update)

```bash
python scripts/extract_inventory.py   # docx → inventory.json + page-slots.json (image-boundary slots)
python scripts/verify_slots.py        # print expected text per slot (optional sanity check)
python scripts/apply_content.py       # apply inventory to HTML via slot manifests
python scripts/validate_content.py    # must exit 0 before considering migration complete
```

Source doc: `Experts Self Publishing Content (New).docx`

`scripts/audit_content.py` delegates to `validate_content.py`.

## Image-boundary extraction

`extract_inventory.py` parses the docx paragraph stream and splits copy at **embedded screenshot boundaries** (119 PNG mockups). Each text block between images maps to an HTML section slot (hero → about-1 → CTA → make-unique → our-service → FAQ).

- Full image map: `content/image-placement-map.json`
- Extracted screenshots: `content/docx-images/<page>/`
- Slot manifests (auto-generated): `content/page-slots.json` (loaded by `scripts/page_slots.py`)

## Slot-based apply

- Per-page slot maps: `content/page-slots.json` (regenerated on every extract)
- [`scripts/apply_content.py`](../scripts/apply_content.py) reads slots from inventory or `page-slots.json`
- Hero prefix pages (`ghostwriting.html`, `book-video-trailers.html`) use fixed HTML prefixes + doc title line
- Page-specific `our-service` headers come from each page's doc chunk (not home copy)
- Validation report: [`content/validation-report.md`](validation-report.md)

## Automated checks

### Slot alignment + old UBP phrases
- **Result:** PASS on all 18 core pages (`python scripts/validate_content.py` exits 0)
- CTA copy verified in `section.cta-sec` for pages with doc CTA lines

### Known gaps (warnings only, not failures)

| Page | Gap |
|------|-----|
| `pricing.html` | CTA block — no CTA copy in doc (hero only) |
| `pricing.html` / `book-publishing.html` | Package card bodies — not in doc |
| `creative-writing.html` | Doc text still contains author-website paragraphs (lines 289–302 in source doc) |

### Branding
- Sitewide rebrand to **Experts Self Publishing** (titles, body copy, footers, forms, email, social links)
- Domain and form endpoints use `expertsselfpublishing.com`
- Asset folder `assets/img/ubp-new/` unchanged (internal path only)

## Deliverables

| Deliverable | Path |
|-------------|------|
| Full paragraph inventory | `content/inventory.json` |
| Slot manifests (generated) | `content/page-slots.json` |
| Slot loader | `scripts/page_slots.py` |
| Image placement map | `content/image-placement-map.json` |
| Apply script | `scripts/apply_content.py` |
| Validation script | `scripts/validate_content.py` |
| Slot preview | `scripts/verify_slots.py` |
| Testimonials reference | `content/testimonials.json` |
| Backups | `*.html.bak` |

## Out of scope (unchanged)

`blogs/*`, `order-details/*`, legal pages, `contact-us.html`, `book-writing.html`, guide landing pages
