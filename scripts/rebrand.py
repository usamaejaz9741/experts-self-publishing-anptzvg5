"""One-shot sitewide rebrand: United Book Publishing -> Experts Self Publishing."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEXT_EXTENSIONS = {".html", ".py", ".md", ".json", ".js", ".yaml", ".yml", ".css", ".bak"}

# Order matters: longer / more specific patterns first.
REPLACEMENTS: list[tuple[str, str]] = [
    (
        "Copyright © 2026 United Book Publishing - All Rights Reserved | Powered By Iota Digital, LLC",
        "Copyright © 2026 Experts Self Publishing. All rights reserved.",
    ),
    (
        "Copyright © 2026 United Book Publishing - All Rights Reserved | Powered By\n"
        "                    Iota Digital, LLC",
        "Copyright © 2026 Experts Self Publishing. All rights reserved.",
    ),
    (
        "Copyright © 2026 United Book Publishing - All Rights Reserved | Powered By",
        "Copyright © 2026 Experts Self Publishing. All rights reserved.",
    ),
    ("United Book Publishing Company", "Experts Self Publishing"),
    ("United%20Book%20Publishing", "Experts%20Self%20Publishing"),
    ("United Book Publishing", "Experts Self Publishing"),
    ("UnitedBookPublishing", "ExpertsSelfPublishing"),
    ("unitedbookpublishing", "expertsselfpublishing"),
    ("United book publishing", "Experts Self publishing"),
]

COPYRIGHT_RE = re.compile(
    r"Copyright © 2026 United Book Publishing[^\n<]*(?:\n\s*Iota Digital, LLC)?",
    re.MULTILINE,
)
MULTILINE_UBP = re.compile(
    r"United(?:\s+Book\s*\n\s*|\s*\n\s*Book\s+)Publishing",
    re.MULTILINE,
)

UBP_REPLACEMENTS: list[tuple[str, str]] = [
    ("United Book Publishers", "Experts Self Publishing"),
    ("United Publishing", "Experts Self Publishing"),
    ("united publishing", "Experts Self Publishing"),
    ("UBP people", "Experts Self Publishing team"),
    ("UBP's", "Experts Self Publishing's"),
    ("UBP\u2019s", "Experts Self Publishing's"),
    ("With UBP,", "With Experts Self Publishing,"),
    ("With UBP's", "With Experts Self Publishing's"),
    ("Choosing UBP", "Choosing Experts Self Publishing"),
    ("When you choose UBP,", "When you choose Experts Self Publishing,"),
    ("choose UBP,", "choose Experts Self Publishing,"),
    (">UBP</span>", ">Experts Self Publishing</span>"),
    ("                                UBP</span>", "Experts Self Publishing</span>"),
]
JULIAN_TESTIMONIAL_RE = re.compile(
    r"My experience is two-fold, from bad to extremely good\. Two United nitwits first\s+"
    r"published my book without consulting me\.\s*"
    r"It was full of errors\. It all changed when Jeffrey Collins, Author Success Manager,\s+"
    r"took charge of my account\.\s*"
    r"He is a master of his trade, and (?:United Book Publishing|Experts Self Publishing) (?:Company )?successfully\s+"
    r"republished my book\. I have self-published\s+"
    r"eight other books with various companies, but United gets the gold\.",
    re.DOTALL,
)
JULIAN_TESTIMONIAL_NEW = (
    "My publishing journey had a difficult beginning, but everything improved once my account "
    "was assigned to a dedicated manager. The team quickly resolved the issues, republished my "
    "book with great care, and delivered results that exceeded my expectations. After publishing "
    "several books over the years, I can confidently say this has been one of my best experiences."
)


def rebrand_text(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = MULTILINE_UBP.sub("Experts Self Publishing", text)
    for old, new in UBP_REPLACEMENTS:
        text = text.replace(old, new)
    text = JULIAN_TESTIMONIAL_RE.sub(JULIAN_TESTIMONIAL_NEW, text)
    text = COPYRIGHT_RE.sub(
        "Copyright © 2026 Experts Self Publishing. All rights reserved.",
        text,
    )
    # Remove orphaned Iota Digital footer lines left after partial copyright fixes.
    text = re.sub(
        r"(Copyright © 2026 Experts Self Publishing\. All rights reserved\.)\s*\n\s*Iota Digital, LLC",
        r"\1",
        text,
    )
    return text


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name in {"rebrand.py", "apply_content.py", "page_slots.py", "extract_inventory.py"}:
            continue
        files.append(path)
    return files


def main() -> None:
    changed = 0
    for path in iter_files():
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = rebrand_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
            print(f"updated: {path.relative_to(ROOT)}")
    print(f"\nDone. {changed} file(s) updated.")


if __name__ == "__main__":
    main()
