from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_CSV_PATH = Path(__file__).resolve().parents[2] / "output" / "sections_v2.csv"
REQUIRED_DOC_TYPES = {"full", "interim"}
NULL_MARKERS = {"", "na", "n/a", "nan", "none", "null"}


def is_nullish(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in NULL_MARKERS


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "chapter_title" not in reader.fieldnames:
            raise ValueError(f"{csv_path} does not contain a chapter_title column")
        return list(reader)


def summarize_missing(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    missing = [row for row in rows if is_nullish(row.get("chapter_title"))]
    unexpected = [row for row in missing if row.get("doc_type", "").strip().lower() in REQUIRED_DOC_TYPES]

    by_doc_type: dict[str, int] = {}
    for row in missing:
        doc_type = row.get("doc_type", "").strip() or "(blank)"
        by_doc_type[doc_type] = by_doc_type.get(doc_type, 0) + 1

    return missing, unexpected, by_doc_type


def print_sample(rows: list[dict[str, str]], limit: int) -> None:
    for row in rows[:limit]:
        print(
            "  "
            f"section_id={row.get('section_id', '')}, "
            f"doc_id={row.get('doc_id', '')}, "
            f"doc_type={row.get('doc_type', '')}, "
            f"section_number={row.get('section_number', '')}, "
            f"section_role={row.get('section_role', '')}"
        )


def check_chapter_title_nullity(csv_path: Path, sample_limit: int) -> int:
    rows = load_rows(csv_path)
    missing, unexpected, by_doc_type = summarize_missing(rows)

    print(f"Checked: {csv_path}")
    print(f"Total rows: {len(rows)}")
    print(f"Rows with null/blank chapter_title: {len(missing)}")

    if by_doc_type:
        print("\nMissing chapter_title by doc_type:")
        for doc_type, count in sorted(by_doc_type.items()):
            print(f"  {doc_type}: {count}")

    if unexpected:
        print(f"\nFAIL: {len(unexpected)} full/interim rows have null/blank chapter_title.")
        print_sample(unexpected, sample_limit)
        return 1

    print("\nPASS: no full/interim rows have null/blank chapter_title.")

    amendment_missing = len(missing) - len(unexpected)
    if amendment_missing:
        print(f"Note: {amendment_missing} amendment/other rows have blank chapter_title.")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check chapter_title nullity in sections_v2.csv.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"CSV file to check. Defaults to {DEFAULT_CSV_PATH}",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=20,
        help="Maximum number of failing rows to print.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return check_chapter_title_nullity(args.csv_path, args.sample_limit)


if __name__ == "__main__":
    raise SystemExit(main())
