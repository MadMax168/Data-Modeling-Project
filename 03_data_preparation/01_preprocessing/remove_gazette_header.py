#!/usr/bin/env python3
"""Remove Gazette header pattern from Thai text data.

Pattern examples removed:
- ตอนที่ 30 เล่ม 27 ราชกิจจานุเบกษา 10 พฤษภาคม 2536
- 345 ตอนที่ 30 เล่ม 23 ราชกิจจานุเบกษา 10 พฤษภาคม 2499
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

DATE_PART = r"[0-9๐-๙]{1,2}\s+\S+\s+[0-9๐-๙]{4}"

# 1) Optional page number before ตอนที่ + (เล่ม|เรื่อง)
PATTERN_TONTEE = (
    r"(?:^|\s)(?:[0-9๐-๙]{1,3}(?:\s+[0-9๐-๙]{1,3})?\s+)?"
    r"ตอนที่\s*[0-9๐-๙]+\s+(?:เล่ม|เรื่อง)\s*[0-9๐-๙]+\s+"
    r"ราชกิจจานุเบกษา\s+(?:วัน(?:ที่)?\s+)?"
    rf"{DATE_PART}(?=\s|$)"
)

# 2) เล่ม/หน้า ... ราชกิจจานุเบกษา ... วันที่ ...
PATTERN_VOLUME_PAGE = (
    r"(?:^|\s)เล่ม\s*[0-9๐-๙]+\s+หน้า\s*[0-9๐-๙]+\s+ราชกิจจานุเบกษา\s+"
    r"(?:วัน(?:ที่)?\s+)?"
    rf"{DATE_PART}(?=\s|$)"
)

# 3) ราชกิจจานุเบกษา ... เล่ม/หน้า ... (วันที่ optional)
PATTERN_GAZETTE_THEN_VOLUME = (
    r"(?:^|\s)ราชกิจจานุเบกษา\s+เล่ม\s*[0-9๐-๙]+\s+หน้า\s*[0-9๐-๙]+"
    r"(?:\s+วัน(?:ที่)?\s+"
    rf"{DATE_PART})?(?=\s|$)"
)

# 4) วัน... ราชกิจจานุเบกษา เล่ม... หน้า...
PATTERN_DATE_THEN_GAZETTE = (
    r"(?:^|\s)(?:วัน(?:ที่)?|วัน\w+ที่)\s+"
    rf"{DATE_PART}\s+ราชกิจจานุเบกษา\s+เล่ม\s*[0-9๐-๙]+\s+หน้า\s*[0-9๐-๙]+(?=\s|$)"
)

# 5) ฉบับพิเศษ หน้า ... ตอนที่ ... เล่ม ...
PATTERN_SPECIAL_ISSUE = (
    r"(?:^|\s)ฉบับพิเศษ\s+หน้า\s*[0-9๐-๙]+\s+ตอนที่\s*[0-9๐-๙]+\s+"
    r"เล่ม\s*[0-9๐-๙]+\s+ราชกิจจานุเบกษา\s+(?:วัน(?:ที่)?\s+)?"
    rf"{DATE_PART}(?=\s|$)"
)

GAZETTE_HEADER_RE = re.compile(
    "|".join(
        [
            PATTERN_TONTEE,
            PATTERN_VOLUME_PAGE,
            PATTERN_GAZETTE_THEN_VOLUME,
            PATTERN_DATE_THEN_GAZETTE,
            PATTERN_SPECIAL_ISSUE,
        ]
    )
)

FALLBACK_GAZETTE_RE = re.compile(
    r"(?:^|\s).{0,48}?"
    r"(?:ฉบับพิเศษ|ตอนที่|เล่ม(?:ที่)?|เรื่อง|หน้า|วัน(?:ที่)?)"
    r".{0,48}?ราชกิจจานุเบกษา.{0,56}?"
    r"(?:[0-9๐-๙]{1,2}\s+\S+\s+[0-9๐-๙-]{3,4}|[0-9๐-๙]{4})(?=\s|$)",
    re.DOTALL,
)


AGGRESSIVE_FRAGMENT_RE = re.compile(
    r"(?:^|\s)"
    r"(?:ฉบับพิเศษ|ตอนที่|เล่ม(?:ที่)?|เรื่อง|หน้า)"
    r".{0,36}?"
    r"ราชกิจจานุเบกษา"
    r"(?:.{0,20}?(?:[0-9๐-๙]{1,4}|วัน(?:ที่)?))?"
    r"(?=\s|$)",
    re.DOTALL,
)

SPECIAL_PAGE_ONLY_RE = re.compile(
    r"(?:^|\s)ฉบับพิเศษ\s+หน้า\s*[0-9๐-๙]{1,4}(?=\s|$)"
)


def clean_text(text: str, aggressive: bool = False) -> str:
    cleaned = text
    for _ in range(2):
        cleaned = GAZETTE_HEADER_RE.sub(" ", cleaned)
    cleaned = FALLBACK_GAZETTE_RE.sub(" ", cleaned)
    if aggressive:
        cleaned = AGGRESSIVE_FRAGMENT_RE.sub(" ", cleaned)
        cleaned = SPECIAL_PAGE_ONLY_RE.sub(" ", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip()


def clean_csv(input_path: Path, output_path: Path, column: str, aggressive: bool) -> None:
    with input_path.open("r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("CSV has no header row")
        if column not in fieldnames:
            raise ValueError(f"Column '{column}' not found. Available: {fieldnames}")

        rows = list(reader)

    for row in rows:
        value = row.get(column, "")
        row[column] = clean_text(value, aggressive=aggressive) if value else value

    with output_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def clean_txt(input_path: Path, output_path: Path, aggressive: bool) -> None:
    text = input_path.read_text(encoding="utf-8")
    output_path.write_text(clean_text(text, aggressive=aggressive), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove Thai Gazette header pattern from CSV or text files"
    )
    parser.add_argument("input", type=Path, help="Input file path (.csv or .txt)")
    parser.add_argument("output", type=Path, help="Output file path")
    parser.add_argument(
        "--column",
        default="text",
        help="Text column name for CSV input (default: text)",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Also remove short/noisy Gazette fragments (OCR-heavy data)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    suffix = args.input.suffix.lower()

    if suffix == ".csv":
        clean_csv(args.input, args.output, args.column, args.aggressive)
    else:
        clean_txt(args.input, args.output, args.aggressive)


if __name__ == "__main__":
    main()
