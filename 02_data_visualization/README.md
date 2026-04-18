# 02 — Data Visualization

Exploratory Data Analysis (EDA) of Thai Constitution text data — 38 constitutions spanning Thai Buddhist years 2475–2564 (1932–2021 CE), containing 4,706 sections.

---

## Input Data

| File | Description |
|---|---|
| `data/preprocessed_data.csv` | Preprocessed output from `01_data_preparation` — 4,706 rows, tokenized |

**Columns:** `constitution_id`, `year_th`, `name_short`, `chapter_number`, `section_number`, `text`, `tokens`, `word_count`

---

## Notebooks

### `notebooks/basic_eda.ipynb`
Foundational structural and lexical exploration.

| Section | Content |
|---|---|
| 1. Data Loading | Load CSV, parse tokens, inspect schema |
| 2. Structural EDA | Section counts, text length distributions per constitution |
| 3. Tokenization | Word count distributions |
| 4. Bag-of-Words | Top 20 most frequent tokens |
| 5. N-Gram Analysis | Top 20 bigrams and trigrams |
| 6. TF-IDF (Global) | Top 20 distinctive words; interactive n-gram slider |
| 7. Per-Constitution TF-IDF | Distinctive words per constitution; interactive dropdown |
| 8. Timeline Analysis | Sections, text length, word count, TTR over time |
| 9. Cross-Constitution Similarity | 38×38 cosine similarity heatmap, ranked pairs, clustermap |
| 10. Word Cloud | All-corpus cloud; interactive per-constitution cloud |

---

### `notebooks/advance_eda.ipynb`
Deeper structural and comparative analysis.

| Section | Content |
|---|---|
| 1. Chapter Structure | Section density heatmap (chapter × constitution); violin plot of section numbers per chapter |
| 2. Era Comparison | Box plots by historical era (interim vs full); timeline with interim shading |
| 3. Vocabulary Evolution | Cumulative vocab growth curve; bump chart of top-word ranks over time |
| 4. KWIC Explorer | Interactive keyword-in-context search (±5 token window) |
| 5. Rare Word Analysis | Frequency spectrum, hapax pie chart, exclusive rare words per constitution |

---

### `notebooks/topic_modelling.ipynb`
Unsupervised theme discovery. *(in progress)*

| Section | Content |
|---|---|
| LDA Topic Modeling | Train LDA, coherence tuning, top keywords per topic, pyLDAvis |
| Topic Distribution Over Time | Stacked bar + line chart of topic proportions per constitution |
| Section-Level Labeling | Dominant topic per section, heatmap across chapter × constitution |

---

## Dependencies

```
pandas
numpy
matplotlib
seaborn
scikit-learn
scipy
wordcloud
ipywidgets
networkx
```

Thai font `LINESeedSansTH_Rg.ttf` is required for correct rendering — located at `static/font/`.

---

## Reference

See [`data_visualization.md`](data_visualization.md) for the full implementation checklist.
