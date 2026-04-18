# Data Visualization Checklist

## Dataset

- **Source:** `data/preprocessed_data.csv`
- **Shape:** 4,706 rows × 8 columns
- **Columns:** `constitution_id`, `year_th`, `name_short`, `chapter_number`, `section_number`, `text`, `tokens`, `word_count`
- **Scope:** 38 constitutions, Thai Buddhist years 2475–2564

---

## `basic_eda.ipynb`

Foundational structural and lexical exploration of the corpus.

### Data Loading & Cleaning
- [x] Load preprocessed CSV and parse `tokens` column from string
- [x] Inspect schema (`df.info()`, `df.nunique()`)
- [x] Identify constitutions with parenthetical variants (interim, amended, No.X)

### Structural EDA
- [x] Bar chart — number of sections per constitution
- [x] Histogram + KDE — distribution of section text lengths (characters)
- [x] Box plot — overall section text length distribution
- [x] Box plot — text length per constitution

### Tokenization
- [x] Histogram + KDE — word count distribution per section
- [x] Box plot — overall word count distribution
- [x] Box plot — word count per constitution

### Bag-of-Words (BoW)
- [x] Bar chart — top 20 most frequent tokens (all corpus)

### N-Gram Analysis
- [x] Bar chart — top 20 bigrams (all corpus)
- [x] Bar chart — top 20 trigrams (all corpus)

### TF-IDF (Global)
- [x] Bar chart — top 20 globally distinctive words by mean TF-IDF score
- [x] Interactive slider widget — explore top TF-IDF n-grams (n=1–10)

### Per-Constitution TF-IDF
- [x] Grid of bar charts — top 10 distinctive words for first 3 constitutions
- [x] Interactive dropdown — explore top 10 distinctive words for any constitution

### Timeline Analysis
- [x] 4-panel chart — total sections, avg text length, avg word count, unique vocab size over time
- [x] Line chart — Type-Token Ratio (TTR / lexical richness) over constitutional history

### Cross-Constitution Similarity
- [x] Heatmap — 38×38 pairwise cosine similarity matrix (TF-IDF)
- [x] Table — top 15 most similar and top 10 least similar pairs
- [x] Clustermap — hierarchically clustered similarity matrix

### Word Cloud
- [x] Word cloud — all constitutions combined (top 200 words)
- [x] Interactive dropdown — word cloud for any single constitution

---

## `advance_eda.ipynb`

Deeper structural and comparative analysis beyond surface-level counts.

### Chapter Structure
- [x] Heatmap — `chapter_number` × `constitution` (section density per chapter per constitution)
- [x] Violin plot — `section_number` distribution grouped by `chapter_number`

### Era Comparison
- [x] Box plot — section text length grouped by historical era (pre-WWII / Cold War / Modern / Democracy Era), split by interim vs full
- [x] Overlay timeline charts with `axvspan` shading for interim constitutions

### Vocabulary Evolution
- [x] Line chart — cumulative unique token count as sections are added chronologically (vocabulary growth curve)
- [x] Line chart — vocabulary growth with constitution boundaries annotated
- [x] Bump chart — rank of top 10 words across constitutions over time

### KWIC Explorer
- [x] Interactive KWIC explorer — search a keyword, display ±5 token context from matching sections

### Rare Word Analysis
- [x] Log-scale frequency spectrum — how many words appear N times
- [x] Pie chart — vocabulary split into hapax (×1), low-freq (×2–5), common (>5)
- [x] 3×3 grid — top 15 exclusive rare words per constitution (first 9 chronologically)
- [x] Interactive dropdown + top-N slider — explore exclusive rare words for any constitution

---

## `topic_modelling.ipynb`

Unsupervised discovery of latent themes across constitutional sections.

### LDA Topic Modeling
- [ ] Train LDA on all tokenized sections (`sklearn` or `gensim`)
- [ ] Choose optimal number of topics (perplexity / coherence score plot)
- [ ] Bar charts — top keywords per topic
- [ ] `pyLDAvis` interactive topic visualization

### Topic Distribution Over Time
- [ ] Stacked bar chart — topic proportion per constitution, sorted chronologically
- [ ] Line chart — dominant topic share per constitution over time

### Section-Level Topic Labeling
- [ ] Assign dominant topic to each section row
- [ ] Heatmap — topic distribution across `chapter_number` × `constitution`
- [ ] Table — representative sections (highest probability) for each topic

---

## Libraries

| Library | Used in |
|---|---|
| `pandas`, `numpy` | all notebooks |
| `matplotlib`, `seaborn` | all notebooks |
| `sklearn TfidfVectorizer`, `cosine_similarity` | basic_eda, advance_eda |
| `pythainlp` | preprocessing (upstream) |
| `wordcloud` | basic_eda |
| `ipywidgets` | basic_eda, advance_eda |
| `scipy` (clustermap) | basic_eda |
| `collections.Counter` | advance_eda |
| `sklearn LDA` / `gensim` | topic_modelling |
| `pyLDAvis` | topic_modelling |
| `LINESeedSansTH` font | all notebooks |
