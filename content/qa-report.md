# Sitewide Content Migration — QA Report

**Date:** 2026-07-17  
**Scope:** 18 core marketing HTML pages

## Content pipeline (use after every docx update)

```bash
python scripts/extract_inventory.py   # docx → content/inventory.json
python scripts/verify_slots.py        # print expected text per slot (optional sanity check)
python scripts/apply_content.py       # apply inventory to HTML via PAGE_SLOTS manifests
python scripts/validate_content.py    # must exit 0 before considering migration complete
```

`scripts/audit_content.py` delegates to `validate_content.py`.

## Slot-based apply

- Per-page slot maps live in [`scripts/page_slots.py`](../scripts/page_slots.py)
- [`scripts/apply_content.py`](../scripts/apply_content.py) uses explicit inventory indices (not blind sequential consumption)
- Validation report: [`content/validation-report.md`](validation-report.md)

## Automated checks

### Slot alignment + old UBP phrases
- **Result:** PASS on all 18 core pages (`python scripts/validate_content.py` exits 0)
- CTA copy verified in `section.cta-sec` for pages with doc CTA lines

### Known gaps (warnings only, not failures)

| Page | Gap |
|------|-----|
| `pricing.html` | CTA block — no CTA copy in doc (hero only) |
| `book-video-trailers.html` | CTA block — no dedicated CTA lines in doc |
| `creative-writing.html` | CTA block — no dedicated CTA lines in doc |
| `children-book-illustration.html` | CTA block — no dedicated CTA lines in doc |
| `screenplay-script-writing.html` | CTA block — no dedicated CTA lines in doc |
| `pricing.html` / `book-publishing.html` | Package card bodies — not in doc |

### Branding
- No visible "United Book Publishing" in body copy on core pages
- `unitedbookpublishing.com` URLs remain in forms/CDN per original plan

## Deliverables

| Deliverable | Path |
|-------------|------|
| Full paragraph inventory | `content/inventory.json` |
| Slot manifests | `scripts/page_slots.py` |
| Apply script | `scripts/apply_content.py` |
| Validation script | `scripts/validate_content.py` |
| Slot preview | `scripts/verify_slots.py` |
| Testimonials reference | `content/testimonials.json` |
| Backups | `*.html.bak` |

## Out of scope (unchanged)

`blogs/*`, `order-details/*`, legal pages, `contact-us.html`, `book-writing.html`, guide landing pages
