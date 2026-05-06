"""
fix_sections_v2.py — Fix duplicate section_ids in sections_v2.csv
=================================================================
Root cause: Thai amendments add sub-articles (มาตรา 48 ทวิ, มาตรา 48 ตรี, ...)
but the upstream splitter only keyed on the base section number, so all
sub-articles collapse to the same section_id as the base article.

Fix: detect the Thai ordinal suffix at the start of each section's text and
append it as a slug to section_id and section_number.

Output: 04_finalize_data/output/sections_v2_fixed.csv
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "03_data_preparation" / "output" / "sections_v2.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_CSV = OUTPUT_DIR / "sections_v2_fixed.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Thai ordinals in canonical order (longest first to avoid prefix ambiguity)
# Each maps to a short ASCII slug used in section_id
ORDINAL_SLUGS = [
    ("เอกนวีสติ",  "19"),
    ("อัฏฐารส",   "18"),
    ("สัตตรส",    "17"),
    ("โสฬส",      "16"),
    ("ปัณรส",     "15"),
    ("จตุทศ",     "14"),
    ("เตรส",      "13"),
    ("ทวาทศ",     "12"),
    ("เอกาทศ",    "11"),
    ("ทศ",        "10"),
    ("นว",        "9"),
    ("อัฏฐ",      "8"),
    ("สัปต",      "7"),
    ("ฉ",         "6"),
    ("เบ็ญจ",     "5"),
    ("เบญจ",      "5"),
    ("จัตวา",     "4"),
    ("ตรี",       "3"),
    ("ทวิ",       "2"),
]

# Pre-compiled: match ordinal at the very start of the (stripped) text
_ORDINAL_RE = re.compile(
    r"^(" + "|".join(re.escape(o) for o, _ in ORDINAL_SLUGS) + r")\s"
)

_ORDINAL_TO_SLUG = {o: s for o, s in ORDINAL_SLUGS}


def _ordinal_slug(text: str) -> str | None:
    """Return the slug for the Thai ordinal prefix, or None if not present."""
    m = _ORDINAL_RE.match(text.strip())
    if not m:
        return None
    return _ORDINAL_TO_SLUG[m.group(1)]


def fix(input_csv: Path, output_csv: Path) -> None:
    with open(input_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Track (doc_id, base_section_number) → count of rows seen so far
    # and which slugs have already been assigned (to handle repeated ordinals).
    seen_count: dict[tuple[str, str], int] = {}
    seen_slugs: dict[tuple[str, str], set[str]] = {}
    fixed_rows = []

    for row in rows:
        key = (row["doc_id"], row["section_number"])
        count = seen_count.get(key, 0)

        if count == 0:
            # First time seeing this (doc_id, section_number) — base article, no change
            seen_count[key] = 1
            seen_slugs[key] = set()
            fixed_rows.append(row)
            continue

        # Duplicate — this is a sub-article; detect ordinal from text
        slug = _ordinal_slug(row["text"])
        used = seen_slugs[key]

        if slug is None or slug in used:
            # No ordinal detected, or same ordinal appears twice — use counter fallback
            slug = str(count + 1)
            while slug in used:
                slug = str(int(slug) + 1)

        used.add(slug)
        new_id = f"{row['section_id']}_{slug}"
        row = dict(row)
        row["section_id"] = new_id
        seen_count[key] = count + 1
        fixed_rows.append(row)

    # Verify no remaining duplicates
    from collections import Counter
    ids = [r["section_id"] for r in fixed_rows]
    remaining_dups = [x for x, c in Counter(ids).items() if c > 1]

    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(fixed_rows)

    print(f"Input rows : {len(rows)}")
    print(f"Output rows: {len(fixed_rows)}  (should be same)")
    print(f"Remaining duplicate section_ids: {len(remaining_dups)}")
    if remaining_dups:
        print("  !", remaining_dups[:10])
    else:
        print("  All section_ids are now unique.")
    print(f"\nWritten → {output_csv}")


if __name__ == "__main__":
    fix(INPUT_CSV, OUTPUT_CSV)
