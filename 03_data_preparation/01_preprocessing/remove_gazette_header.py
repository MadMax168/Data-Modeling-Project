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

# 1) Optional 1-3 digit page number before "ตอนที่" will be removed too.
PATTERN_TONTEE = (
    r"(?:^|\s)"
    r"(?:[0-9๐-๙]{1,3}(?:\s+[0-9๐-๙]{1,3})?\s+)?"  # page number, e.g. "345" or "3 47"
    r"ตอนที่\s*[0-9๐-๙]+\s+"
    r"(?:เล่ม|เรื่อง)\s*[0-9๐-๙]+\s+"
    r"ราชกิจจานุเบกษา\s+[0-9๐-๙]{1,2}\s+\S+\s+[0-9๐-๙]{4}"
    r"(?=\s|$)"
)

# 2) "เล่ม 49 หน้า 536 ราชกิจจานุเบกษา วันที่ 10 ธันวาคม 2475"
PATTERN_VOLUME_PAGE = (
    r"(?:^|\s)เล่ม\s*[0-9๐-๙]+\s+หน้า\s*[0-9๐-๙]+\s+ราชกิจจานุเบกษา\s+วัน(?:ที่)?\s+[0-9๐-๙]{1,2}\s+\S+\s+[0-9๐-๙]{4}(?=\s|$)"
)

GAZETTE_HEADER_RE = re.compile(f"(?:{PATTERN_TONTEE}|{PATTERN_VOLUME_PAGE})")


def clean_text(text: str) -> str:
    cleaned = GAZETTE_HEADER_RE.sub(" ", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" *\\n *", "\\n", cleaned)
    return cleaned.strip()


def clean_csv(input_path: Path, output_path: Path, column: str) -> None:
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
        row[column] = clean_text(value) if value else value

    with output_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def clean_txt(input_path: Path, output_path: Path) -> None:
    text = input_path.read_text(encoding="utf-8")
    output_path.write_text(clean_text(text), encoding="utf-8")


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    suffix = args.input.suffix.lower()

    if suffix == ".csv":
        clean_csv(args.input, args.output, args.column)
    else:
        clean_txt(args.input, args.output)


if __name__ == "__main__":
    main()
