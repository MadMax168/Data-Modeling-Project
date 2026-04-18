# Data Visualization — Current Ideas

## Overview

Exploratory Data Analysis (EDA) of Thai Constitution data, covering 38 constitutions (Thai Buddhist years 2475–2564) with 4,706 sections across 31 distinct years.

## Dataset

- **Source:** `01_data_preparation/struc-data/csv/all_sections_combined.csv`
- **Shape:** 4,706 rows × 6 columns
- **Columns:** `constitution_id`, `year_th`, `name_short`, `chapter_number`, `section_number`, `section_text`
- **Key stats:** 38 unique constitutions, 336 unique section numbers, 18 chapter levels
- **Notable:** 13 constitutions have variants (interim, amended, No.2–4)

## Analysis Sections

### 1. Data Loading and Cleaning
- Strip `"Constitution"` prefix from `name_short` for cleaner labels
- Identify and flag constitutions with parenthetical variants (interim, amended, numbered revisions)

### 2. Basic Structural EDA
- **Volume analysis:** Bar chart of section counts per constitution — shows which constitutions are more detailed
- **Text length distribution:** Histogram with KDE of character counts per section — reveals how verbose individual sections are

### 3. Thai Tokenization and Preprocessing
- Compare two tokenization engines: `newmm` vs `attacut` (via PyThaiNLP)
- Use `attacut` as the primary engine for final tokenization
- Remove Thai stopwords (PyThaiNLP corpus) and punctuation/symbols
- Visualize word count distribution per section after cleaning

### 4. Bag-of-Words (BoW) Analysis
- Aggregate all tokens across the entire corpus
- Bar chart of top 20 most frequent words — surface the most common constitutional vocabulary

### 5. N-Gram Analysis
- Compute top 20 bigrams and trigrams across the full corpus
- Subplots for bigrams and trigrams side-by-side — reveals common multi-word legal phrases

### 6. TF-IDF Analysis
- Vectorize tokenized text using `TfidfVectorizer` with pre-tokenized input
- Plot top 20 distinctive words by mean TF-IDF score — identifies terms that are important but not universally common
- **Interactive widget:** `ipywidgets` slider (n=1–10) to dynamically explore top TF-IDF n-grams at any granularity

## Tools & Libraries

| Tool | Purpose |
|---|---|
| `pandas` | Data loading and manipulation |
| `matplotlib` / `seaborn` | Static visualizations |
| `pythainlp` | Thai tokenization and stopword removal |
| `sklearn TfidfVectorizer` | TF-IDF computation |
| `ipywidgets` | Interactive n-gram explorer |
| `LINESeedSansTH` font | Thai character rendering in plots |

## Next Ideas / Gaps

- Per-constitution TF-IDF comparison (distinctive words per era, not global)
- Topic modeling (LDA or BERTopic) to cluster sections by theme
- Timeline analysis — how vocabulary/length evolves across constitutional history
- Cross-constitution similarity heatmap
- Named entity / legal term extraction
