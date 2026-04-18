# Data Modeling Project

Analysis of Thai Constitution text data — exploring the structure, vocabulary, and evolution of 38 constitutions spanning Thai Buddhist years 2475–2564 (1932–2021 CE).

---

## Project Structure

```
Data-Modeling-Project/
├── 01_data_preparation/       # Data parsing and preprocessing
├── 02_data_visualization/     # EDA and visualization notebooks
├── data/
│   └── preprocessed_data.csv  # Tokenized dataset
├── static/
│   └── font/
│       └── LINESeedSansTH_Rg.ttf
└── pyproject.toml
```

---

## Dataset

**`data/preprocessed_data.csv`** — 4,706 rows, one row per constitutional section.

| Column              | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `constitution_id` | Unique constitution identifier (e.g.`const_2475`)     |
| `year_th`         | Year in Thai Buddhist Era                               |
| `name_short`      | Short name (e.g.`2475`, `2490 (interim)`)           |
| `chapter_number`  | Chapter number (0 = general, -1 = transitory)           |
| `section_number`  | Section number                                          |
| `text`            | Raw section text (Thai)                                 |
| `tokens`          | Tokenized and cleaned word list (PyThaiNLP `attacut`) |
| `word_count`      | Number of tokens after cleaning                         |

---

## Stages

### `01_data_preparation`

Parses raw JSON output from the PDF extraction pipeline into structured JSON and flat CSV.

- Cleans Royal Gazette headers/footers
- Normalizes Thai numerals to Arabic
- Extracts preamble, chapters, and sections
- Tokenizes text using PyThaiNLP and removes stopwords

See [`01_data_preparation/README.md`](01_data_preparation/README.md) for details.

### `02_data_visualization`

EDA across three notebooks:

| Notebook                  | Focus                                                                     |
| ------------------------- | ------------------------------------------------------------------------- |
| `basic_eda.ipynb`       | Structural counts, BoW, n-grams, TF-IDF, similarity, word clouds          |
| `advance_eda.ipynb`     | Chapter structure, era comparison, vocabulary evolution, rare words, KWIC |
| `topic_modelling.ipynb` | LDA topic modeling*(in progress)*                                       |

See [`02_data_visualization/README.md`](02_data_visualization/README.md) for details.

---

## Setup

Requires Python 3.12+. Dependencies are managed with [uv](https://github.com/astral-sh/uv).

```bash
# Install dependencies
uv sync

# Activate virtual environment (bash) (Optional)
source .venv/Scripts/activate

# Launch Jupyter (Optional)
jupyter lab 
```
