from __future__ import annotations

import argparse
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = PREP_ROOT / "output" / "sections_v2.csv"
DEFAULT_OUTPUT_PATH = PREP_ROOT / "output" / "chapter_title_counts.png"
DEFAULT_COUNTS_PATH = PREP_ROOT / "output" / "chapter_title_counts.csv"
DEFAULT_FONT_PATH = PROJECT_ROOT / "static" / "font" / "LINESeedSansTH_Rg.ttf"

os.environ.setdefault("MPLCONFIGDIR", str(PREP_ROOT / "output" / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager


NULL_LABEL = "(ไม่มีหมวด)"


def load_sections(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    required_columns = {"chapter_title", "doc_type"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{csv_path} is missing required column(s): {missing}")
    return df


def chapter_counts(df: pd.DataFrame, include_blank: bool, doc_types: set[str] | None) -> pd.DataFrame:
    if doc_types:
        normalized = df["doc_type"].fillna("").astype(str).str.strip().str.lower()
        df = df[normalized.isin(doc_types)].copy()

    titles = df["chapter_title"].fillna("").astype(str).str.strip()
    if include_blank:
        titles = titles.mask(titles == "", NULL_LABEL)
    else:
        titles = titles[titles != ""]

    counts = titles.value_counts().rename_axis("chapter_title").reset_index(name="section_count")
    return counts.sort_values(["section_count", "chapter_title"], ascending=[False, True]).reset_index(drop=True)


def configure_thai_font(font_path: Path) -> font_manager.FontProperties | None:
    if not font_path.exists():
        return None

    font_manager.fontManager.addfont(str(font_path))
    font_properties = font_manager.FontProperties(fname=str(font_path))
    plt.rcParams["font.family"] = font_properties.get_name()
    plt.rcParams["axes.unicode_minus"] = False
    return font_properties


def plot_counts(counts: pd.DataFrame, output_path: Path, font_properties: font_manager.FontProperties | None) -> None:
    plot_df = counts.sort_values("section_count", ascending=True)
    fig_height = max(8, len(plot_df) * 0.35)
    fig, ax = plt.subplots(figsize=(14, fig_height))

    bars = ax.barh(plot_df["chapter_title"], plot_df["section_count"], color="#2f6f8f")
    ax.set_title("จำนวนมาตราในแต่ละหมวด", fontproperties=font_properties, fontsize=18, pad=16)
    ax.set_xlabel("จำนวนมาตรา", fontproperties=font_properties, fontsize=12)
    ax.set_ylabel("หมวด", fontproperties=font_properties, fontsize=12)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if font_properties:
        for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_fontproperties(font_properties)

    max_count = int(plot_df["section_count"].max()) if not plot_df.empty else 0
    ax.set_xlim(0, max_count * 1.08 if max_count else 1)
    for bar in bars:
        width = int(bar.get_width())
        ax.text(
            width + max_count * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{width}",
            va="center",
            fontproperties=font_properties,
            fontsize=10,
        )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def parse_doc_types(value: str) -> set[str] | None:
    if value.lower() == "all":
        return None
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a chart of section counts by chapter_title.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"CSV file to chart. Defaults to {DEFAULT_CSV_PATH}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"PNG output path. Defaults to {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--counts-output",
        type=Path,
        default=DEFAULT_COUNTS_PATH,
        help=f"CSV counts output path. Defaults to {DEFAULT_COUNTS_PATH}",
    )
    parser.add_argument(
        "--doc-types",
        default="full,interim",
        help="Comma-separated doc_type values to include, or 'all'. Defaults to full,interim.",
    )
    parser.add_argument(
        "--include-blank",
        action="store_true",
        help="Include blank chapter_title values as '(ไม่มีหมวด)'.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    df = load_sections(args.csv_path)
    counts = chapter_counts(df, include_blank=args.include_blank, doc_types=parse_doc_types(args.doc_types))
    if counts.empty:
        print("No chapter_title values found for the selected filters.")
        return 1

    args.counts_output.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(args.counts_output, index=False, encoding="utf-8-sig")

    font_properties = configure_thai_font(DEFAULT_FONT_PATH)
    plot_counts(counts, args.output, font_properties)

    print(f"Chart saved to: {args.output}")
    print(f"Counts saved to: {args.counts_output}")
    print(f"Chapter titles counted: {len(counts)}")
    print(f"Sections counted: {int(counts['section_count'].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
