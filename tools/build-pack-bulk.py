#!/usr/bin/env python3
"""
Build the offline pack from Open Food Facts' full CSV export.

The API route caps out fast (503s after a few thousand rows), so this reads the
bulk export instead. It streams straight from stdin and never stores the 1.2 GB
file — pipe it in:

    curl -sL <export-url> | python3 tools/build-pack-bulk.py 50000

Keeps the N most-scanned products, since scan count is the best available proxy
for "something a person will actually point a phone at". Rows stay as arrays to
keep the shipped file small:

    code: [name, brand, score, grade, co2_per_kg]
"""

import csv
import gzip
import json
import os
import sys

TOP_N = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
OUT = "pack.json"

csv.field_size_limit(10_000_000)

COLS = {}
rows = []          # (scans, code, name, brand, score, grade, co2)
seen = 0
kept = 0


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


stream = gzip.GzipFile(fileobj=sys.stdin.buffer)
reader = csv.reader((line.decode("utf-8", "replace") for line in stream), delimiter="\t")

header = next(reader)
for i, name in enumerate(header):
    COLS[name] = i


def get(row, col):
    i = COLS.get(col)
    if i is None or i >= len(row):
        return ""
    return row[i].strip()


CO2_COLS = [
    "product_quantity",  # placeholder, replaced below if a carbon column exists
]
for cand in ("carbon-footprint-from-known-ingredients_100g", "carbon-footprint_100g"):
    if cand in COLS:
        CO2_COLS = [cand]
        break

for row in reader:
    seen += 1
    if seen % 250_000 == 0:
        print(f"  read {seen:,} rows, kept {len(rows):,}", flush=True)

    code = get(row, "code")
    name = get(row, "product_name")
    if not code or not name or len(code) < 6:
        continue

    scans = num(get(row, "unique_scans_n")) or 0
    score = num(get(row, "environmental_score_score"))
    grade = get(row, "environmental_score_grade")[:1].lower()
    if grade not in "abcde":
        grade = ""

    # only worth shipping if it is popular or actually carries a score
    if scans < 1 and score is None:
        continue

    co2 = None
    for c in CO2_COLS:
        v = num(get(row, c))
        if v is not None:
            co2 = round(v / 100.0, 2) if c.endswith("_100g") else round(v, 2)
            break

    brand = get(row, "brands").split(",")[0].strip()[:26]
    rows.append((scans, code, " ".join(name.split())[:44], brand,
                 int(score) if score is not None else None, grade, co2))
    kept += 1

print(f"\nscanned {seen:,} products, {kept:,} candidates")

rows.sort(key=lambda r: -r[0])
rows = rows[:TOP_N]

pack = {r[1]: [r[2], r[3], r[4], r[5], r[6]] for r in rows}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(pack, f, ensure_ascii=False, separators=(",", ":"))

scored = sum(1 for v in pack.values() if v[2] is not None)
size = os.path.getsize(OUT) / 1024 / 1024
print(f"wrote {OUT}: {len(pack):,} products, {scored:,} scored, {size:.1f} MB")
