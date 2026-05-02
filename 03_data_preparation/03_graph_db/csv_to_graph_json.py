import csv
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent.parent
CSV_PATH = ROOT / "03_data_preparation" / "output" / "sections_v2.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_PATH = OUTPUT_DIR / "sections_graph.json"


# ── helpers ──────────────────────────────────────────────────────────────────

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def find_items(text: str) -> list[dict]:
    """
    Split text into top-level items (1)(2)(3)... and detect references inside each.

    Top-level item: the next expected sequential number starting from 1.
    A candidate (n) is skipped if it is preceded (within 30 chars) by 'มาตรา X'
    or by 'หรือ' — meaning it belongs to a reference chain, not a new item.
    """
    token_matches = list(re.finditer(r'\((\d+)\)', text))
    tokens = [(m.start(), m.end(), int(m.group(1))) for m in token_matches]

    if not tokens or tokens[0][2] != 1:
        return []

    def has_thai_text_after(token_end: int) -> bool:
        # look at up to 3 chars right after token — if Thai text follows, it's a top-level item
        window = text[token_end:token_end + 3]
        return bool(re.search(r'[ก-๙]', window))

    item_positions = []
    next_expected = 1
    for start, end, num in tokens:
        if num == next_expected and has_thai_text_after(end):
            item_positions.append((start, num))
            next_expected += 1

    if len(item_positions) < 2:
        return []

    items = []
    for idx, (start, num) in enumerate(item_positions):
        end = item_positions[idx + 1][0] if idx + 1 < len(item_positions) else len(text)
        item_text = text[start + len(f'({num})'):end].strip()
        items.append({
            "item_id": None,
            "number": num,
            "text": item_text,
            "references": find_references(item_text),
        })

    return items


def find_references(text: str) -> list[dict]:
    """
    Detect patterns like 'ตามมาตรา 107 (1)(2)(3)' or 'มาตรา 92' in item text.
    Returns list of {section_number, items[]} — doc_id resolved by caller.
    """
    refs = []
    # match: มาตรา <number> optionally followed by (n)(n)... and หรือ (n)
    pattern = re.compile(
        r'มาตรา\s+(\d+)'                      # มาตรา X
        r'((?:\s*(?:หรือ\s*)?\(\d+\))*)'       # optional (n)(n)... หรือ (n)
    )
    for m in pattern.finditer(text):
        section_num = int(m.group(1))
        sub_items_str = m.group(2)
        sub_items = [int(x) for x in re.findall(r'\((\d+)\)', sub_items_str)]
        refs.append({
            "section_number": section_num,
            "items": sub_items,
        })
    return refs


# ── main transform ────────────────────────────────────────────────────────────

def load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_sections(rows: list[dict]) -> list[dict]:
    seen_ids = set()
    sections = []

    for row in rows:
        section_id = row["section_id"]
        if section_id in seen_ids:
            continue
        seen_ids.add(section_id)

        text = row["text"]
        items = find_items(text)
        doc_id = row["doc_id"]

        # resolve section_id into item-level references
        for item in items:
            item["item_id"] = f"{section_id}_i_{item['number']}"
            for ref in item["references"]:
                ref["section_id"] = f"{doc_id}_s_{ref['section_number']}"

        # section-level references: mาตรา mentions in text that are NOT inside items
        # strip item portion from text to avoid double-counting
        if items:
            # text before the first item
            first_item_start = text.index(f'({items[0]["number"]})')
            text_before_items = text[:first_item_start]
        else:
            text_before_items = text
        section_refs = find_references(text_before_items)
        for ref in section_refs:
            ref["section_id"] = f"{doc_id}_s_{ref['section_number']}"

        sub_num = safe_int(row["sub_section_number"])
        target_sec = safe_int(row["target_section_no"])
        target_ch = safe_int(row["target_chapter"])

        section = {
            "section_id": section_id,
            "doc_id": doc_id,
            "doc_type": row["doc_type"],
            "year_th": safe_int(row["year_th"]),
            "year_ce": safe_int(row["year_ce"]),
            "name_short": row["name_short"],
            "era": row["era"],
            "regime_type": row["regime_type"],
            "parent_doc_id": row["parent_doc_id"] or None,
            "chapter_number": safe_int(row["chapter_number"]),
            "chapter_title": row["chapter_title"] or None,
            "section_number": safe_int(row["section_number"]),
            "section_role": row["section_role"],
            "change_mode": row["change_mode"],
            "text": text,
        }

        if sub_num is not None:
            section["sub_section_number"] = sub_num
            section["sub_section_title"] = row["sub_section_title"] or None

        if target_sec is not None:
            section["target_section_no"] = target_sec

        if target_ch is not None:
            section["target_chapter"] = target_ch

        if section_refs:
            section["references"] = section_refs

        if items:
            section["items"] = items

        sections.append(section)

    return sections


def print_summary(sections: list[dict]):
    total = len(sections)
    with_items = sum(1 for s in sections if s.get("items"))
    with_sub = sum(1 for s in sections if s.get("sub_section_number") is not None)
    total_items = sum(len(s["items"]) for s in sections if s.get("items"))
    item_refs = sum(
        len(item["references"])
        for s in sections if s.get("items")
        for item in s["items"]
    )
    section_refs = sum(len(s["references"]) for s in sections if s.get("references"))
    amendment_sections = sum(1 for s in sections if s.get("target_section_no") is not None)

    print("=== Graph JSON Summary ===")
    print(f"  Sections total              : {total}")
    print(f"  Sections with items         : {with_items}")
    print(f"  Sections with sub_section   : {with_sub}")
    print(f"  Total items parsed          : {total_items}")
    print(f"  References (in items)       : {item_refs}")
    print(f"  References (section-level)  : {section_refs}")
    print(f"  Amendment targets           : {amendment_sections}")
    print(f"  Output                      : {OUTPUT_PATH}")


def main():
    rows = load_csv(CSV_PATH)
    sections = build_sections(rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

    print_summary(sections)


if __name__ == "__main__":
    main()
