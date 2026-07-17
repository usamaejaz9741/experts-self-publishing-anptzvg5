"""Debug docx block order (text vs images)."""
import html
import re
import zipfile
from pathlib import Path

DOCX = Path(__file__).resolve().parent.parent / "Experts Self Publishing Content (New).docx"

with zipfile.ZipFile(DOCX) as zf:
    xml = zf.read("word/document.xml").decode("utf-8")
    rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")

rid_map = {m.group(1): m.group(2) for m in re.finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)}

blocks = []
for raw in re.split(r"</w:p>", xml):
    plain = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
    imgs = []
    for e in re.findall(r'r:embed="(rId\d+)"', raw):
        t = rid_map.get(e, "")
        if "media/" in t:
            imgs.append(t.split("/")[-1])
    if plain or imgs:
        blocks.append(("img" if imgs and not plain else "text", plain[:70] if plain else imgs))

# show author-website region (around image8)
for i, (kind, val) in enumerate(blocks):
    if i < 15:
        print(f"{i:3} {kind:4} {val}")
