"""
parser_2495.py — Custom parser for const_2495
===============================================
รัฐธรรมนูญแห่งราชอาณาจักรไทย พุทธศักราช ๒๔๗๕ แก้ไขเพิ่มเติม พุทธศักราช ๒๔๙๕

โครงสร้างพิเศษ: แก้ไขระดับ "หมวด" ทั้งหมวด ไม่ใช่มาตราเดียว
- มาตรา wrapper (1-11) = คำสั่งแก้ไข เช่น "ความในหมวด 2 ให้แก้ไขดังนี้"
- quoted sections (38-123) = เนื้อหาใหม่ที่ insert เข้ามา อยู่ภายใน wrapper

Strategy:
  - แยก wrapper sections ออกจาก quoted sections ด้วย position-based logic
  - wrapper = มาตรา N ที่มีเลขน้อย (≤ 15) และ position อยู่ก่อน quoted block
  - quoted = มาตรา N ที่มีเลขใหญ่ และอยู่ระหว่าง wrapper สองตัว
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Thai numeral → Arabic
# ---------------------------------------------------------------------------
_THAI_MAP = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def _to_arabic(s: str) -> str:
    return s.translate(_THAI_MAP)


# ---------------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------------
# จับมาตรา (รองรับเลขไทยและอารบิก)
_RE_SECTION_MARKER = re.compile(r"\nมาตรา\s+([๐-๙\d]+)[.\s]")

# change_mode patterns (ระดับหมวด)
_RE_CHAPTER_AMEND = re.compile(r"ความในหมวด\s*[\d๐-๙]+")
_RE_CHAPTER_REPEAL = re.compile(r"ให้ยกเลิก(?:ความใน)?หมวด\s*[\d๐-๙]+.{0,100}?ทั้งหมวด")
_RE_CHAPTER_NEW = re.compile(r"ให้เพิ่มความ.{0,60}?เป็นหมวด\s*[\d๐-๙]+")

# target หมวดจาก wrapper
_RE_CHAPTER_NO = re.compile(r"หมวด\s*([๐-๙\d]+)")

# มาตรา wrapper = reinstate entire constitution (มาตรา 1 ของ 2495)
_RE_REINSTATE = re.compile(r"ให้ใช้รัฐธรรมนูญ")


def classify_wrapper(sec_no: int, text: str) -> tuple[str, str]:
    """
    Returns (change_mode, target_chapter_or_section)
    change_mode: meta / reinstate / chapter_amended / chapter_repealed /
                 chapter_new / renumber / content
    """
    if sec_no == 1 and _RE_REINSTATE.search(text):
        return "reinstate", ""

    if sec_no == 11:
        # มาตรา 11 = renumber (ปรับเลขมาตรา)
        return "renumber", ""

    if _RE_CHAPTER_REPEAL.search(text):
        chapters = _RE_CHAPTER_NO.findall(text)
        target = _to_arabic(chapters[0]) if chapters else ""
        return "chapter_repealed", target

    if _RE_CHAPTER_NEW.search(text):
        chapters = _RE_CHAPTER_NO.findall(text)
        target = _to_arabic(chapters[0]) if chapters else ""
        return "chapter_new", target

    if _RE_CHAPTER_AMEND.search(text):
        chapters = _RE_CHAPTER_NO.findall(text)
        target = _to_arabic(chapters[0]) if chapters else ""
        return "chapter_amended", target

    return "content", ""


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------
def parse_2495(full_text: str) -> list[dict]:
    """
    Parse const_2495 full_text into rows.

    Returns list of dicts with keys:
        section_number, section_role, change_mode,
        target_chapter, text
    """
    # Normalize Thai numerals and whitespace
    text = _to_arabic(full_text)
    text = re.sub(r"[ \t]+", " ", text)

    # Find all มาตรา markers with their positions
    markers = [(m.start(), int(m.group(1).translate(_THAI_MAP)))
               for m in _RE_SECTION_MARKER.finditer(text)]

    if not markers:
        return []

    # Separate wrapper (1-11) vs quoted sections (>= 30)
    # Heuristic: wrapper sections appear in order 1,2,3,...11 interleaved with quoted blocks
    # We identify wrapper by: section_number <= 15
    wrapper_positions = [(pos, sec) for pos, sec in markers if sec <= 15]
    quoted_positions  = [(pos, sec) for pos, sec in markers if sec > 15]

    rows = []

    # --- Process wrapper sections ---
    # Wrapper text = from start of marker to next wrapper marker
    # (quoted sections in between are part of that wrapper's content but we track them separately)
    all_wrapper_pos = [pos for pos, _ in wrapper_positions]

    for i, (pos, sec_no) in enumerate(wrapper_positions):
        # end = next wrapper start (skip over quoted sections in between)
        next_wrapper_pos = wrapper_positions[i + 1][0] if i + 1 < len(wrapper_positions) else len(text)

        # Wrapper text = everything from this marker up to first quoted section
        # OR up to next wrapper if no quoted section follows
        quoted_in_range = [(p, s) for p, s in quoted_positions if pos < p < next_wrapper_pos]

        if quoted_in_range:
            wrapper_end = quoted_in_range[0][0]
        else:
            wrapper_end = next_wrapper_pos

        # Extract wrapper instruction text (without quoted block)
        wrapper_text = re.sub(r"\s+", " ", text[pos:wrapper_end]).strip()
        # Remove the "มาตรา N " prefix
        wrapper_text = re.sub(rf"^มาตรา\s+{sec_no}\s*", "", wrapper_text).strip()

        change_mode, target_chapter = classify_wrapper(sec_no, wrapper_text)

        rows.append({
            "section_number": sec_no,
            "section_role": "wrapper",
            "change_mode": change_mode,
            "target_chapter": target_chapter,
            "target_section_no": "",
            "text": wrapper_text,
        })

        # --- Process quoted sections inside this wrapper ---
        for j, (q_pos, q_sec) in enumerate(quoted_in_range):
            q_end = quoted_in_range[j + 1][0] if j + 1 < len(quoted_in_range) else next_wrapper_pos
            q_text = re.sub(r"\s+", " ", text[q_pos:q_end]).strip()
            q_text = re.sub(rf"^มาตรา\s+{q_sec}\s*", "", q_text).strip()

            rows.append({
                "section_number": q_sec,
                "section_role": "quoted",
                "change_mode": "new_content",   # เนื้อหาใหม่ที่ถูก insert
                "target_chapter": target_chapter,
                "target_section_no": str(q_sec),
                "text": q_text,
            })

    return rows


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    d = json.load(open("01_data_preparation/data/const_2495.json"))
    rows = parse_2495(d.get("full_text", ""))

    print(f"Total rows: {len(rows)}")
    print(f"Wrappers : {sum(1 for r in rows if r['section_role'] == 'wrapper')}")
    print(f"Quoted   : {sum(1 for r in rows if r['section_role'] == 'quoted')}")
    print()

    print(f"{'role':8s} {'sec':>5s} {'change_mode':20s} {'target_ch':>9s} {'text preview'}")
    print("-" * 90)
    for r in rows:
        print(
            f"{r['section_role']:8s} "
            f"{r['section_number']:>5d} "
            f"{r['change_mode']:20s} "
            f"{r['target_chapter']:>9s} "
            f"{r['text'][:55]}"
        )
