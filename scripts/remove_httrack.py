"""Remove HTTrack mirror comments and delete HTTrack artifact files."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEXT_EXTENSIONS = {".html", ".bak", ".css", ".js", ".md"}

HTTRACK_COMMENT_RE = re.compile(
    r"<!--\s*(?:Mirrored from .*? by HTTrack|Created by HTTrack)[^>]*-->\s*",
    re.IGNORECASE | re.DOTALL,
)
HTTRACK_META_RE = re.compile(
    r"<!--\s*Added by HTTrack\s*-->.*?<!--\s*/Added by HTTrack\s*-->\s*",
    re.IGNORECASE | re.DOTALL,
)

# Directories that only exist as HTTrack redirect/stub trees.
HTTRACK_DIRS = [
    ROOT / "signals",
    ROOT / "schema.org",
    ROOT / "public",
]

# Single-file HTTrack stubs at repo root.
HTTRACK_ROOT_FILES = [
    "e.html",
    "t.html",
    "n.html",
    "o.html",
    "t-2.html",
    "n-2.html",
    "info@expertsselfpublishing.html",
]

# HTTrack error-page clones under assets/ and blog asset mirrors.
HTTRACK_ASSET_GLOBS = [
    "assets/**/*.html",
    "blogs/assets/**/*.html",
    "order-details/assets/**/*.html",
    "blogs/Experts Self Publishing.html",
    "blogs/United Book Publishing.html",
]


def strip_httrack_markup(text: str) -> str:
    text = HTTRACK_COMMENT_RE.sub("", text)
    text = HTTRACK_META_RE.sub("", text)
    # Collapse extra blank lines introduced at the top of documents.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def is_httrack_stub(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return False
    if "<title>NOT FOUND</title>" in head:
        return True
    if "Page has moved" in head and "HTTrack" in head:
        return True
    if path.name in HTTRACK_ROOT_FILES and path.parent == ROOT:
        return True
    return False


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name == "remove_httrack.py":
            continue
        files.append(path)
    return files


def delete_httrack_artifacts() -> list[Path]:
    removed: list[Path] = []

    for rel in HTTRACK_ROOT_FILES:
        path = ROOT / rel
        if path.is_file():
            path.unlink()
            removed.append(path)

    for pattern in HTTRACK_ASSET_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                path.unlink()
                removed.append(path)

    for directory in HTTRACK_DIRS:
        if directory.exists():
            shutil.rmtree(directory)
            removed.append(directory)

    return removed


def main() -> None:
    changed = 0
    for path in iter_text_files():
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = strip_httrack_markup(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
            print(f"cleaned: {path.relative_to(ROOT)}")

    removed = delete_httrack_artifacts()
    for path in removed:
        print(f"deleted: {path.relative_to(ROOT)}")

    print(f"\nDone. Cleaned {changed} file(s), deleted {len(removed)} path(s).")


if __name__ == "__main__":
    main()
