"""Fix HTTrack .html asset stubs and fetch missing images from the source site."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "https://unitedbookpublishing.com"

TEXT_EXTENSIONS = {".html", ".bak"}

# HTTrack saved missing assets as .html stubs under local mirror paths.
NESTED_ASSET_FIXES: list[tuple[str, str]] = [
    ("assets/img/favicon/apple-touch-icon.html", "../assets/img/favicon/apple-touch-icon.png"),
    ("assets/img/favicon/favicon-32x32.html", "../assets/img/favicon/favicon-32x32.png"),
    ("assets/img/ubp-new/banner-bg.html", "../assets/img/ubp-new/banner-bg.webp"),
    ("assets/font/oswald-f/Oswald-Regular.html", "../assets/font/oswald-f/Oswald-Regular.woff2"),
    ('src="assets/img/badge-discount.html"', 'src="../assets/img/badge-discount.png"'),
    ('src="assets/img/popup-image.html"', 'src="../assets/img/popup-image.png"'),
    ('src="assets/img/contact-bann.webp"', 'src="../assets/img/contact-bann.webp"'),
]

ROOT_ASSET_FIXES: list[tuple[str, str]] = [
    ("assets/img/underlay-2.html", "assets/img/underlay.png"),
]


def fix_nested_asset_refs(text: str) -> str:
    for old, new in NESTED_ASSET_FIXES:
        text = text.replace(old, new)
    return text


def fix_root_asset_refs(text: str) -> str:
    for old, new in ROOT_ASSET_FIXES:
        text = text.replace(old, new)
    return text


def iter_html_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if "__pycache__" in path.parts:
            continue
        files.append(path)
    return files


def fix_html_files() -> int:
    changed = 0
    for path in iter_html_files():
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = original
        rel = path.relative_to(ROOT)
        if rel.parts[0] in {"blogs", "order-details"}:
            updated = fix_nested_asset_refs(updated)
        else:
            updated = fix_root_asset_refs(updated)
        if updated != original:
            try:
                path.write_text(updated, encoding="utf-8", newline="\n")
            except OSError as exc:
                print(f"skip write {rel}: {exc}")
                continue
            changed += 1
            print(f"fixed refs: {rel}")
    return changed


def collect_missing_paths() -> list[str]:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from audit_assets import collect_refs, resolve_ref

    missing: set[str] = set()
    for source, ref in collect_refs():
        target = resolve_ref(source, ref)
        if target is None or target.exists():
            continue
        key = str(target.relative_to(ROOT)).replace("\\", "/")
        if key.endswith(".html"):
            continue
        missing.add(key)
    return sorted(missing)


def download_asset(rel_path: str) -> bool:
    dest = ROOT / rel_path.replace("/", "\\")
    if dest.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{SOURCE}/{rel_path}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                return False
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                return False
            dest.write_bytes(response.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False
    print(f"downloaded: {rel_path}")
    return True


def main() -> None:
    changed = fix_html_files()
    print(f"\nFixed asset refs in {changed} file(s).")

    downloaded = 0
    failed: list[str] = []
    for rel_path in collect_missing_paths():
        if download_asset(rel_path):
            downloaded += 1
        else:
            failed.append(rel_path)

    print(f"\nDownloaded {downloaded} asset(s).")
    if failed:
        print(f"Still missing ({len(failed)}):")
        for path in failed:
            print(f"  {path}")


if __name__ == "__main__":
    main()
