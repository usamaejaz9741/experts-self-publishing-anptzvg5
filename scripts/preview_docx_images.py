"""Extract sample images from the content docx for inspection."""
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "Experts Self Publishing Content (New).docx"
OUT = ROOT / "content" / "docx-preview"
OUT.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(DOCX) as zf:
    xml = zf.read("word/document.xml").decode("utf-8")
    rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
    rid_to_media = {}
    for match in re.finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels_xml):
        rid_to_media[match.group(1)] = match.group(2)

    order = []
    for match in re.finditer(r'r:embed="(rId\d+)"', xml):
        target = rid_to_media.get(match.group(1), "")
        if "media/" in target:
            order.append(target.split("/")[-1])

    print(f"Images in document order: {len(order)}")
    print("First 15:", order[:15])

    samples = [order[0], order[2], order[5], order[10], order[20], order[-1]]
    for name in dict.fromkeys(samples):
        dest = OUT / name
        dest.write_bytes(zf.read(f"word/media/{name}"))
        print(f"Extracted {name}")
