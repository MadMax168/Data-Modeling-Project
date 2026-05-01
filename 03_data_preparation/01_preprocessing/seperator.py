from __future__ import annotations

import csv
from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "sections_v2.csv"
OUTPUT_DIR = BASE_DIR / "output" / "sections_v2_by_year"
DOC_ID_PATTERN = re.compile(r"const_(\d{4}[a-z]?)$", re.IGNORECASE)


def load_sections_csv(csv_path: Path) -> pd.DataFrame:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected = len(header)
        fixed_rows: list[list[str]] = []

        for line_no, row in enumerate(reader, start=2):
            if len(row) == expected:
                fixed_rows.append(row)
                continue

            if len(row) > expected:
                # Unquoted commas in free-text fields spill into extra columns.
                fixed_rows.append(row[: expected - 1] + [",".join(row[expected - 1 :])])
                print(
                    f"[warn] repaired line {line_no}: "
                    f"{len(row)} -> {expected} columns (merged tail into text)"
                )
                continue

            fixed_rows.append(row + [""] * (expected - len(row)))
            print(f"[warn] repaired line {line_no}: {len(row)} -> {expected} columns (padded missing fields)")

    return pd.DataFrame(fixed_rows, columns=header)


def main() -> None:
    df = load_sections_csv(INPUT_CSV)

    if "year_th" not in df.columns:
        raise ValueError("Missing required column: year_th")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for (year, doc_id), group_df in df.groupby(["year_th", "doc_id"], sort=True, dropna=False):
        if pd.isna(doc_id):
            if pd.isna(year):
                filename = "unknown.csv"
            else:
                filename = f"{int(year)}.csv"
        else:
            doc_text = str(doc_id).strip()
            match = DOC_ID_PATTERN.fullmatch(doc_text)
            if match:
                filename = f"{match.group(1).lower()}.csv"
            elif pd.isna(year):
                filename = f"{doc_text}.csv"
            else:
                filename = f"{int(year)}_{doc_text}.csv"

        output_path = OUTPUT_DIR / filename
        group_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Wrote {len(group_df):,} rows -> {output_path}")


if __name__ == "__main__":
    main()
