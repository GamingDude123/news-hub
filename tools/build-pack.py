#!/usr/bin/env python3
"""
Build an offline pack of the most-scanned products from Open Food Facts.

The live API covers ~4.6M products, which is far more than can ship inside a
web app. This grabs the head of that distribution — the items people actually
scan — so common groceries resolve instantly and without a network round trip.
Anything not in the pack still falls through to the live lookup.

Rows are arrays rather than objects purely to keep the file small:
    code: [name, brand, ecoscore, grade, co2_per_kg]

Usage:  python3 tools/build-pack.py [pages]      (100 products per page)
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 50
OUT = "pack.json"
FIELDS = "code,product_name,brands,ecoscore_score,ecoscore_grade,ecoscore_data"
BASE = "https://world.openfoodfacts.org/api/v2/search"


def fetch(page):
    qs = urllib.parse.urlencode({
        "sort_by": "unique_scans_n",
        "page_size": 100,
        "page": page,
        "fields": FIELDS,
    })
    req = urllib.request.Request(f"{BASE}?{qs}", headers={"User-Agent": "EcoTrace/1.0 pack builder"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def clean(s, limit):
    if not s:
        return ""
    s = " ".join(str(s).split())
    if "," in s:
        s = s.split(",")[0].strip()
    return s[:limit]


pack = {}
for page in range(1, PAGES + 1):
    for attempt in range(3):
        try:
            data = fetch(page)
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == 2:
                print(f"page {page}: giving up ({e})", file=sys.stderr)
                data = {"products": []}
            else:
                time.sleep(3)

    products = data.get("products") or []
    if not products:
        continue

    for p in products:
        code = str(p.get("code") or "").strip()
        name = clean(p.get("product_name"), 44)
        if not code or not name:
            continue

        score = p.get("ecoscore_score")
        score = score if isinstance(score, (int, float)) else None

        grade = (p.get("ecoscore_grade") or "")[:1]
        if grade not in "abcde":
            grade = ""

        agri = ((p.get("ecoscore_data") or {}).get("agribalyse") or {})
        co2 = agri.get("co2_total")
        co2 = round(co2, 2) if isinstance(co2, (int, float)) else None

        pack[code] = [name, clean(p.get("brands"), 26), score, grade, co2]

    print(f"page {page}/{PAGES} — {len(pack)} products", flush=True)
    time.sleep(0.4)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(pack, f, ensure_ascii=False, separators=(",", ":"))

scored = sum(1 for v in pack.values() if v[2] is not None)
carbon = sum(1 for v in pack.values() if v[4] is not None)
import os
print(f"\nwrote {OUT}: {len(pack)} products, {scored} scored, {carbon} with carbon data, "
      f"{os.path.getsize(OUT)/1024:.0f} KB")
