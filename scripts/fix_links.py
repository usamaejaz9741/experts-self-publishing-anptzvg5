"""Fix HTTrack-broken external URLs and fragile absolute asset links."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEXT_EXTENSIONS = {".html", ".css", ".js", ".bak"}

CDN_FIXES: list[tuple[str, str]] = [
    ("../../cdn.jsdelivr.net/", "https://cdn.jsdelivr.net/"),
    ("../cdn.jsdelivr.net/", "https://cdn.jsdelivr.net/"),
    ("'../../connect.facebook.net/", "'https://connect.facebook.net/"),
    ("'../connect.facebook.net/", "'https://connect.facebook.net/"),
    ('"../../connect.facebook.net/', '"https://connect.facebook.net/'),
    ('"../connect.facebook.net/', '"https://connect.facebook.net/'),
    ("../../cdn.prod.website-files.com/", "https://cdn.prod.website-files.com/"),
    ("../cdn.prod.website-files.com/", "https://cdn.prod.website-files.com/"),
]

SITE = "https://expertsselfpublishing.com"

SLICK_FONT_FACE = """@font-face {
    font-family: 'slick';
    font-weight: normal;
    font-style: normal;
    src: url('https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/fonts/slick.eot');
    src: url('https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/fonts/slick.eot?#iefix') format('embedded-opentype'),
         url('https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/fonts/slick.woff') format('woff'),
         url('https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/fonts/slick.ttf') format('truetype'),
         url('https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/fonts/slick.svg#slick') format('svg');
}"""


def depth_prefix(path: Path) -> str:
    rel = path.relative_to(ROOT)
    if rel.parent == Path("."):
        return ""
    return "/".join([".."] * len(rel.parent.parts))


def relative_site_url(path: Path, url: str) -> str:
    if not url.startswith(SITE):
        return url
    tail = url[len(SITE) :].lstrip("/")
    prefix = depth_prefix(path)

    if not tail:
        return f"{prefix}/index.html" if prefix else "index.html"

    if not Path(tail).suffix and not tail.endswith("/"):
        tail = f"{tail}.html"

    return f"{prefix}/{tail}" if prefix else tail


def fix_html_or_js(path: Path, text: str) -> str:
    for old, new in CDN_FIXES:
        text = text.replace(old, new)

    def repl(match: re.Match[str]) -> str:
        quote = match.group(1)
        url = match.group(2)
        if url.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
            return match.group(0)
        if "/inquiry-submit" in url or "/form-submit" in url:
            return match.group(0)
        if url.startswith(SITE):
            return f"{quote}{relative_site_url(path, url)}{quote}"
        return match.group(0)

    return re.sub(r"""([\"'])(https://expertsselfpublishing\.com[^\"']*)\1""", repl, text)


def fix_css(text: str) -> str:
    for old, new in CDN_FIXES:
        text = text.replace(old, new)
    text = text.replace('.html")', '.png")')
    text = text.replace(".html')", ".png')")
    text = text.replace(".html?#", ".png?#")
    text = text.replace(".html#", ".png#")
    return text


def fix_slick_theme(text: str) -> str:
    return re.sub(
        r"@font-face\s*\{[^}]*font-family:\s*'slick'[^}]*\}",
        SLICK_FONT_FACE,
        text,
        count=1,
        flags=re.DOTALL,
    )


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name == "fix_links.py":
            continue
        files.append(path)
    return files


def main() -> None:
    changed = 0
    for path in iter_files():
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = original
        if path.suffix.lower() in {".html", ".js", ".bak"}:
            updated = fix_html_or_js(path, updated)
            updated = updated.replace("assets/css/style.css?v=15", "assets/css/style8e5e.css?v=15")
            updated = updated.replace("assets/css/responsive.css?v=13", "assets/css/responsivef500.css?v=13")
        if path.suffix.lower() == ".css":
            if path.name in {"jquery-ui.css", "style8e5e.css", "slick-theme.css"}:
                updated = fix_css(updated)
            if path.name == "slick-theme.css":
                updated = fix_slick_theme(updated)
        if path.name == "style8e5e.css":
            updated = updated.replace(
                'url("../images/pf-leaf-about.png")',
                'url("../img/form-leaf.webp")',
            )
            updated = updated.replace(
                'url("../images/pf-leaf-about.html")',
                'url("../img/form-leaf.webp")',
            )
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
            print(f"updated: {path.relative_to(ROOT)}")
    print(f"\nDone. {changed} file(s) updated.")


if __name__ == "__main__":
    main()
