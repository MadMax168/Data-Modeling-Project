from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "sections_v2.csv"
OUTPUT_DIR = BASE_DIR / "output" / "sections_v2_by_year"
DOC_ID_PATTERN = re.compile(r"const_(\d{4}[a-z]?)$", re.IGNORECASE)


def main() -> None:
    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

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
