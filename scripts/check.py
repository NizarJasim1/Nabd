#!/usr/bin/env python3
"""Integrity checks for the static site: HTML parses, JSON is valid, and every
local asset the page references actually exists. Run: python3 scripts/check.py"""
import html.parser, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
fail = []


def check_html(name):
    text = (ROOT / name).read_text(encoding="utf-8")

    class P(html.parser.HTMLParser):
        pass
    try:
        P().feed(text)
    except Exception as e:  # noqa: BLE001
        fail.append(f"{name}: HTML did not parse: {e}")
    # local asset references (ignore http(s), data:, mailto:, anchors, templating)
    for m in re.findall(r'(?:src|href)="([^"]+)"', text):
        if m.startswith(("http://", "https://", "data:", "mailto:", "#", "${", "{{")):
            continue
        p = (ROOT / m.lstrip("/")).resolve()
        if not p.exists():
            fail.append(f"{name}: missing local asset {m!r}")


def check_json(name):
    try:
        json.loads((ROOT / name).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail.append(f"{name}: invalid JSON: {e}")


for f in ("index.html", "404.html"):
    if (ROOT / f).exists():
        check_html(f)
check_json("manifest.webmanifest")

# icons declared in the manifest must exist
man = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
for icon in man.get("icons", []):
    src = icon.get("src", "")
    if src and not (ROOT / src.lstrip("/")).exists():
        fail.append(f"manifest: missing icon {src!r}")

if fail:
    print("CHECK FAILED:")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("CHECK OK — HTML parses, JSON valid, all local assets present")
