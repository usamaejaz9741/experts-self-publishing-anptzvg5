"""Find missing local assets referenced from HTML/CSS/JS."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

URL_RE = re.compile(r"""url\(["']?([^"')]+)["']?\)""")
SRC_RE = re.compile(
    r"""(?:src|href|data-src|content)=["']([^"']+)["']""",
    re.IGNORECASE,
)

SKIP_PREFIXES = (
    "data:",
    "http://",
    "https://",
    "#",
    "mailto:",
    "tel:",
    "javascript:",
)


def collect_refs() -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".css", ".js"}:
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(ROOT))
        for match in URL_RE.finditer(text):
            ref = match.group(1).split("?")[0].split("#")[0]
            if ref.startswith(SKIP_PREFIXES):
                continue
            refs.add((rel, ref))
        for match in SRC_RE.finditer(text):
            ref = match.group(1).split("?")[0].split("#")[0]
            if ref.startswith(SKIP_PREFIXES):
                continue
            if path.suffix.lower() == ".html" and (
                ref.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".woff", ".woff2", ".ttf", ".eot"))
                or "assets/" in ref
            ):
                refs.add((rel, ref))
    return refs


def resolve_ref(source: str, ref: str) -> Path | None:
    if ref.startswith("/"):
        target = ROOT / ref.lstrip("/")
    else:
        target = (ROOT / source).parent / ref
    try:
        target = target.resolve()
        root = ROOT.resolve()
    except OSError:
        return None
    if root not in target.parents and target != root:
        return None
    return target


def main() -> None:
    missing: dict[str, list[str]] = {}
    for source, ref in sorted(collect_refs()):
        target = resolve_ref(source, ref)
        if target is None or target.exists():
            continue
        key = str(target.relative_to(ROOT)).replace("\\", "/")
        missing.setdefault(key, []).append(source)

    print(f"Missing assets: {len(missing)}")
    for path, sources in sorted(missing.items()):
        print(f"  {path}  (e.g. {sources[0]})")


if __name__ == "__main__":
    main()
