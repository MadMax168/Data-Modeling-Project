"""
data_prep.py — Thai Constitution Data Preparation Pipeline
==========================================================
อ่าน raw JSON จาก 01_data_preparation/data/
แล้วผลิต sections_v2.csv ที่มี:
  - doc_type   : full / interim / amendment
  - change_mode: new / amended / repealed / text_substitution / meta / content
  - target_section_no: มาตราในฉบับหลักที่ถูกแก้ (เฉพาะ amendment)
  - parent_doc_id: ฉบับที่ถูกแก้ไข
"""

import csv
import json
import re
from pathlib import Path

from parser_2495 import parse_2495

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent.parent
INPUT_DIR = ROOT / "01_data_preparation" / "data"
OUTPUT_DIR = ROOT / "03_data_preparation" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Document classification
# ---------------------------------------------------------------------------
# ฉบับที่เป็น full constitution ทั้งชิ้น (ไม่ใช่ amendment)
FULL_DOCS = {
    "const_2475", "const_2489", "const_2492",
    "const_2502", "const_2511", "const_2517", "const_2519",
    "const_2521", "const_2534b", "const_2540",
    "const_2550", "const_2560",
}

# ฉบับ interim charter (ประกาศหลัง coup — full text แต่ไม่ใช่ permanent)
INTERIM_DOCS = {
    "const_2490a", "const_2515", "const_2520",
    "const_2534a", "const_2549", "const_2557",
}

# amendment → parent mapping (แก้ฉบับอะไร)
PARENT_MAP = {
    "const_2482": "const_2475",
    "const_2483": "const_2475",
    "const_2485": "const_2475",
    "const_2495": "const_2475",
    "const_2490b": "const_2490a",
    "const_2491a": "const_2489",
    "const_2491b": "const_2489",
    "const_2515": None,           # interim — ไม่มี parent
    "const_2518": "const_2517",
    "const_2520": None,           # interim — ไม่มี parent
    "const_2528": "const_2521",
    "const_2532": "const_2521",
    "const_2535a": "const_2534b",
    "const_2535b": "const_2534b",
    "const_2535c": "const_2534b",
    "const_2535d": "const_2534b",
    "const_2538": "const_2534b",
    "const_2539": "const_2534b",
    "const_2548": "const_2540",
    "const_2549": None,           # interim — ไม่มี parent
    "const_2554a": "const_2550",
    "const_2554b": "const_2550",
    "const_2564": "const_2560",
}


def get_doc_type(doc_id: str, name_short: str) -> str:
    if doc_id in FULL_DOCS:
        return "full"
    if doc_id in INTERIM_DOCS:
        return "interim"
    # ถ้าอยู่ใน PARENT_MAP แสดงว่าเป็น amendment แน่นอน
    if doc_id in PARENT_MAP:
        return "amendment"
    ns = name_short.lower()
    if "interim" in ns:
        return "interim"
    if any(tag in ns for tag in ["no.", "(no", "amended", "แก้ไข"]):
        return "amendment"
    # fallback: ถ้าไม่รู้จัก ให้เป็น full
    return "full"


# ---------------------------------------------------------------------------
# Text cleaning (นำมาจาก create_clean_dataset.ipynb)
# ---------------------------------------------------------------------------
_HEADER_PATTERNS = [
    re.compile(r'เล่ม\s*[\d๐-๙]+\s*ตอนที่.*?ราชกิจจานุเบกษา[^\n]*'),
    re.compile(r'วัน(?:ที่)?\s*[\d๐-๙]+\s*\S+\s*[\d๐-๙]+\s*ราชกิจจานุเบกษา[^\n]*'),
    re.compile(r'^ราชกิจจานุเบกษา[^\n]*$', re.MULTILINE),
    re.compile(r'^---+$', re.MULTILINE),
    re.compile(r'^\s*[\d๐-๙]+\s*$', re.MULTILINE),
    re.compile(r'^\s*หน้า\s*[\d๐-๙]+\s*$', re.MULTILINE),
    re.compile(r'\[image\]', re.IGNORECASE),
]


def _thai_to_arabic(text: str) -> str:
    return text.translate(str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789"))


def _fix_sara_am(text: str) -> str:
    return re.sub(r"([ก-ฮ])\s+า([ก-ฮ\s])", r"\1ำ\2", text)


def clean_text(raw: str) -> str:
    text = raw
    for pat in _HEADER_PATTERNS:
        text = pat.sub("", text)
    text = _fix_sara_am(text)
    text = _thai_to_arabic(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Amendment parser — detect change_mode + target_section_no
# ---------------------------------------------------------------------------
# Pattern: "ให้ยกเลิกความใน ... มาตรา N ... และให้ใช้ความ..."
_RE_AMEND = re.compile(r"ให้ยกเลิกความใน.{0,60}?มาตรา\s+(\d+).{0,200}?และให้ใช้ความ", re.DOTALL)
# Pattern: "ให้ยกเลิกมาตรา N" หรือ "ให้ยกเลิกบทบัญญัติมาตรา N" (repeal ล้วนๆ ไม่มีแทน)
_RE_REPEAL = re.compile(r"ให้ยกเลิก(?:บทบัญญัติ)?มาตรา\s+(\d+)")
# Pattern: "ให้เพิ่มความ/ให้เพิ่มมาตรา"
_RE_NEW = re.compile(r"ให้เพิ่ม(?:ความ|มาตรา|บทบัญญัติ)")
# Pattern: "ให้ใช้คำว่า X แทน" (text substitution เช่น เปลี่ยนสยาม→ไทย)
_RE_SUBST = re.compile(r"ให้ใช้คำว่า")


def classify_amendment_section(sec_no: int, text: str) -> tuple[str, list[int]]:
    """
    Returns (change_mode, [target_section_numbers])
    change_mode: meta / amended / repealed / new / text_substitution / content
    """
    # มาตรา 1-2 ของทุก amendment = meta (ชื่อฉบับ + วันบังคับใช้)
    if sec_no <= 2:
        return "meta", []

    # ลอง match pattern ต่างๆ
    if _RE_AMEND.search(text):
        # หา target section: เลขมาตราแรกที่ปรากฏหลัง "ให้ยกเลิกความใน"
        m = _RE_AMEND.search(text)
        if m:
            target = int(m.group(1))
            return "amended", [target]
        return "amended", []

    if _RE_REPEAL.search(text):
        targets = [int(n) for n in _RE_REPEAL.findall(text)]
        return "repealed", targets[:1]

    if _RE_NEW.search(text):
        # หา section number ที่ตามมา
        targets = [int(n) for n in re.findall(r"มาตรา\s+(\d+)", text)]
        targets = [t for t in targets if t != sec_no]
        return "new", targets[:1]

    if _RE_SUBST.search(text):
        return "text_substitution", []

    # มาตราที่เป็น quoted replacement text (ขึ้นต้นด้วย " หรือ ')
    stripped = text.strip()
    if stripped.startswith(('"', "'", "\u201c", "\u2018")):
        return "content", []

    return "content", []


# ---------------------------------------------------------------------------
# Section splitter (ใช้กับทั้ง full และ amendment)
# ---------------------------------------------------------------------------
# รองรับ "มาตรา N " และ "มาตรา N." (บางฉบับเก่ามีจุดตามหลัง)
_RE_SECTION_SPLIT = re.compile(r"(?:^|\n)มาตรา\s+(\d+)[.\s]")


def split_sections(text: str) -> list[tuple[int, str]]:
    """Return list of (section_number, section_text)"""
    results = []
    matches = list(_RE_SECTION_SPLIT.finditer(text))
    for i, m in enumerate(matches):
        sec_no = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sec_text = re.sub(r"\s+", " ", text[start:end]).strip()
        if sec_text:
            results.append((sec_no, sec_text))
    return results


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "section_id",
    "doc_id",
    "doc_type",
    "year_th",
    "year_ce",
    "name_short",
    "era",
    "regime_type",
    "parent_doc_id",
    "chapter_number",
    "chapter_title",
    "section_number",
    "section_role",
    "target_chapter",
    "target_section_no",
    "change_mode",
    "text",
]


def process_file(json_path: Path) -> list[dict]:
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    doc_id = raw["id"]
    year_th = raw.get("year_th", 0)
    year_ce = raw.get("year_ce", year_th - 543)
    name_short = raw.get("name_short", "")
    era = raw.get("era", "")
    regime_type = raw.get("regime_type", "")

    doc_type = get_doc_type(doc_id, name_short)
    parent_doc_id = PARENT_MAP.get(doc_id, None) if doc_type == "amendment" else None

    full_text = raw.get("full_text") or "\n\n".join(
        p.get("raw_markdown", "") for p in raw.get("pages", [])
    )
    cleaned = clean_text(full_text)

    rows = []

    if doc_type in ("full", "interim"):
        rows = _parse_full_constitution(cleaned, doc_id, doc_type, year_th, year_ce, name_short, era, regime_type)
    elif doc_id == "const_2491b":
        # 2491b = quoted-only amendment, ไม่มี wrapper มาตรา — treat ทั้งก้อนเป็น new_content
        rows = _parse_quoted_only(cleaned, doc_id, year_th, year_ce, name_short, era, regime_type, parent_doc_id, target_section_no=95)
    elif doc_id == "const_2495":
        # comprehensive amendment — แก้ระดับหมวด ต้องใช้ parser พิเศษ
        rows = _parse_2495(raw.get("full_text", ""), doc_id, year_th, year_ce, name_short, era, regime_type, parent_doc_id)
    else:
        rows = _parse_amendment(cleaned, doc_id, year_th, year_ce, name_short, era, regime_type, parent_doc_id)

    return rows


def _parse_quoted_only(
    text: str, doc_id: str, year_th: int, year_ce: int,
    name_short: str, era: str, regime_type: str,
    parent_doc_id: str | None, target_section_no: int
) -> list[dict]:
    """สำหรับ amendment ที่เป็น quoted block ล้วนๆ ไม่มี wrapper มาตรา"""
    return [{
        "section_id": f"{doc_id}_s_{target_section_no}_quoted",
        "doc_id": doc_id,
        "doc_type": "amendment",
        "year_th": year_th,
        "year_ce": year_ce,
        "name_short": name_short,
        "era": era,
        "regime_type": regime_type,
        "parent_doc_id": parent_doc_id or "",
        "chapter_number": 0,
        "chapter_title": "",
        "section_number": target_section_no,
        "section_role": "quoted",
        "target_chapter": "",
        "target_section_no": str(target_section_no),
        "change_mode": "new_content",
        "text": re.sub(r"\s+", " ", text).strip(),
    }]


def _parse_2495(
    full_text: str, doc_id: str, year_th: int, year_ce: int,
    name_short: str, era: str, regime_type: str, parent_doc_id: str | None
) -> list[dict]:
    parsed = parse_2495(full_text)
    rows = []
    for r in parsed:
        rows.append({
            "section_id": f"{doc_id}_s_{r['section_number']}_{r['section_role']}",
            "doc_id": doc_id,
            "doc_type": "amendment",
            "year_th": year_th,
            "year_ce": year_ce,
            "name_short": name_short,
            "era": era,
            "regime_type": regime_type,
            "parent_doc_id": parent_doc_id or "",
            "chapter_number": 0,
            "chapter_title": "",
            "section_number": r["section_number"],
            "section_role": r["section_role"],
            "target_chapter": r["target_chapter"],
            "target_section_no": r["target_section_no"],
            "change_mode": r["change_mode"],
            "text": r["text"],
        })
    return rows


def _parse_full_constitution(
    text: str, doc_id: str, doc_type: str,
    year_th: int, year_ce: int, name_short: str, era: str, regime_type: str
) -> list[dict]:
    rows = []

    # detect chapters
    _RE_CHAPTER = re.compile(
        r"(?:^|\n)(?:หมวด(?:ที่)?\s*(\d+)\s*(.*)|บท(?:ที่)?\s*(\d+)\s*(.*))$",
        re.MULTILINE,
    )
    _RE_SPECIAL = re.compile(
        r"(?:^|\n)(บททั่วไป|บทเฉพาะ(?:กาล)?|บทบัญญัติเฉพาะ(?:กาล)?|บทนำ)\s*$",
        re.MULTILINE,
    )

    chapter_splits = []
    for m in _RE_SPECIAL.finditer(text):
        title = m.group(1).strip()
        chap_num = 0 if "ทั่วไป" in title or "นำ" in title else -1
        chapter_splits.append((m.start(), chap_num, title))
    for m in _RE_CHAPTER.finditer(text):
        if m.group(1):
            chapter_splits.append((m.start(), int(m.group(1)), m.group(2).strip()))
        elif m.group(3):
            chapter_splits.append((m.start(), int(m.group(3)), m.group(4).strip()))
    chapter_splits.sort(key=lambda x: x[0])

    if not chapter_splits:
        chapter_splits = [(0, 0, "บททั่วไป")]

    for i, (pos, chap_num, chap_title) in enumerate(chapter_splits):
        end = chapter_splits[i + 1][0] if i + 1 < len(chapter_splits) else len(text)
        segment = text[pos:end]
        for sec_no, sec_text in split_sections(segment):
            rows.append({
                "section_id": f"{doc_id}_s_{sec_no}",
                "doc_id": doc_id,
                "doc_type": doc_type,
                "year_th": year_th,
                "year_ce": year_ce,
                "name_short": name_short,
                "era": era,
                "regime_type": regime_type,
                "parent_doc_id": "",
                "chapter_number": chap_num,
                "chapter_title": chap_title,
                "section_number": sec_no,
                "section_role": "content",
                "target_chapter": "",
                "target_section_no": "",
                "change_mode": "content",
                "text": sec_text,
            })

    return rows


def _parse_amendment(
    text: str, doc_id: str, year_th: int, year_ce: int,
    name_short: str, era: str, regime_type: str, parent_doc_id: str | None
) -> list[dict]:
    rows = []
    sections = split_sections(text)

    # ถ้า split ได้น้อยมาก (เช่น text เสีย) ให้ใส่ทั้งก้อนเป็น 1 row
    if not sections:
        rows.append({
            "section_id": f"{doc_id}_s_0",
            "doc_id": doc_id,
            "doc_type": "amendment",
            "year_th": year_th,
            "year_ce": year_ce,
            "name_short": name_short,
            "era": era,
            "regime_type": regime_type,
            "parent_doc_id": parent_doc_id or "",
            "chapter_number": 0,
            "chapter_title": "",
            "section_number": 0,
            "section_role": "content",
            "target_chapter": "",
            "target_section_no": "",
            "change_mode": "content",
            "text": re.sub(r"\s+", " ", text).strip(),
        })
        return rows

    for sec_no, sec_text in sections:
        change_mode, targets = classify_amendment_section(sec_no, sec_text)
        target_str = str(targets[0]) if targets else ""
        rows.append({
            "section_id": f"{doc_id}_s_{sec_no}",
            "doc_id": doc_id,
            "doc_type": "amendment",
            "year_th": year_th,
            "year_ce": year_ce,
            "name_short": name_short,
            "era": era,
            "regime_type": regime_type,
            "parent_doc_id": parent_doc_id or "",
            "chapter_number": 0,
            "chapter_title": "",
            "section_number": sec_no,
            "section_role": "wrapper",
            "target_chapter": "",
            "target_section_no": target_str,
            "change_mode": change_mode,
            "text": sec_text,
        })

    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    json_files = sorted(INPUT_DIR.glob("const_*.json"))
    if not json_files:
        print(f"ไม่พบไฟล์ใน {INPUT_DIR}")
        return

    all_rows = []
    for fp in json_files:
        try:
            rows = process_file(fp)
            all_rows.extend(rows)
            print(f"  {fp.name:30s} → {len(rows):4d} sections  (doc_type={rows[0]['doc_type'] if rows else '?'})")
        except Exception as e:
            print(f"  ERROR {fp.name}: {e}")

    out_path = OUTPUT_DIR / "sections_v2.csv"
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nรวม {len(all_rows)} rows → {out_path}")

    # สรุป stats
    by_type = {}
    by_mode = {}
    for r in all_rows:
        by_type[r["doc_type"]] = by_type.get(r["doc_type"], 0) + 1
        by_mode[r["change_mode"]] = by_mode.get(r["change_mode"], 0) + 1

    print("\n--- doc_type breakdown ---")
    for k, v in sorted(by_type.items()):
        print(f"  {k:20s}: {v}")
    print("\n--- change_mode breakdown ---")
    for k, v in sorted(by_mode.items()):
        print(f"  {k:20s}: {v}")


if __name__ == "__main__":
    main()
