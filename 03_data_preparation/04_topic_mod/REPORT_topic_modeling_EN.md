# Topic Modeling of Thai Constitutional Sections

## 1. Motivation

Thailand's 38 constitutions (B.E. 2475–2564 / 1932–2021) have inconsistent chapter structures across versions — the same subject matter may appear under different chapter names, or the same chapter title may cover different content depending on the constitution. Grouping sections by `chapter_title` or `section_title` alone is therefore insufficient for cross-version comparative analysis.

The goal of this section is to use **topic modeling** to group sections by **semantic content** rather than structural labels. Beyond simple grouping, the approach is designed to show that a single section can carry **partial membership across multiple themes simultaneously** (multi-theme membership) — reflecting the reality that constitutional provisions often address more than one subject within a single article.

**Input:** `sections_v2.csv` — 2,797 sections from 38 constitutions

---

## 2. Methodology Progression

### Attempt 0a — LDA (Latent Dirichlet Allocation)

The first approach was LDA, a classic probabilistic topic model. Text was vectorized using CountVectorizer into a bag-of-words matrix, which LDA then used to discover latent topics.

**Problem:** LDA treats text as word frequency counts with no understanding of semantic meaning. The resulting topics were clusters of co-occurring words rather than coherent constitutional themes. Thai language additionally requires specialized tokenization, making the bag-of-words representation lose even more contextual information.

### Attempt 0b — BERTopic + text-embedding-3-large (OpenRouter)

Switched to BERTopic, which uses dense embeddings instead of bag-of-words. Additional visualizations were produced including an Intertopic Distance Map and Hierarchical Topic Tree to explore topic structure.

**Problem:** The embedding model used was `text-embedding-3-large` — a general-purpose, English-first model. When Thai text is embedded with this model, Thai words are mapped into a vector space optimized for English. Semantically related Thai words may end up far apart in this space, causing the clustering to not reflect actual content relationships.

**Lesson learned:** A Thai-native embedding model pre-trained specifically on Thai text is required.

### Attempt 1 — WangchanBERTa + Unsupervised BERTopic

Switched to **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`), a BERT-based model pre-trained directly on the Thai Common Crawl corpus, combined with unsupervised BERTopic (no seed guidance).

**Result:** 79 topics discovered (excluding outlier -1), but two problems remained:
- 617 sections (22.1%) were assigned to outlier cluster -1 by HDBSCAN — not belonging to any topic
- 79 topics were too granular and difficult to interpret at a meaningful theme level

### Attempt 2 & 3 — Guided BERTopic + Seed Themes

Incorporated domain knowledge of Thai constitutional structure by defining **seed themes** — 14 themes in attempt 2, expanded to 15 in attempt 3 (adding "พรรคการเมืองและการเลือกตั้ง" / Political Parties & Elections) — passed to BERTopic via the `seed_topic_list` parameter.

This produced 101 topics with section-level soft scoring. However, the soft scoring in these attempts used keyword overlap as a heuristic, causing 352 sections (12.8%) with no matching seed keywords to be classified as "อื่น ๆ (emergent)" regardless of their actual content.

### Attempt 4 — Hybrid Soft Scoring (Final)

Addressed the high emergent rate by introducing an embedding-based fallback for sections that keyword scoring could not assign. Detailed in section 3.

---

## 3. Pipeline Detail (Attempt 4)

### 3.1 Preprocessing

`sections_v2.csv` is loaded and tokenized using **AttaCut** (a Thai-specific tokenizer). Three custom stopword groups are then filtered:

- **Group A** — Thai function words (ใน/in, โดย/by, ซึ่ง/which, เพื่อ/for, ...)
- **Group B** — Document structure noise (มาตรา/section, หมวด/chapter, วรรค/paragraph, รัฐธรรมนูญ/constitution, ...)
- **Group C** — Legal boilerplate (กฎหมาย/law, ระเบียบ/regulation, ภายใต้/under, ...)

Group B filtering is particularly important — the word "รัฐธรรมนูญ" (constitution) appears in virtually every section. Without filtering it would dominate all embeddings, making every section appear identical in vector space.

### 3.2 Embedding

Each section is embedded using **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`) with mean-pooling over the last hidden state and L2 normalization, producing a matrix of shape **2,797 × 768** where each row is a dense vector representing the semantic meaning of that section.

```
max_length = 416 tokens
batch_size = 16
device     = MPS (Apple Silicon)
```

### 3.3 Semi-supervised Topic Discovery (Guided BERTopic)

BERTopic orchestrates three sequential components, each configured with custom parameters:

**UMAP** — reduces dimensionality from 768 → 5 while preserving semantic neighborhood structure:
```
n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine'
```

**HDBSCAN** — finds density-based clusters in the 5D space without requiring a fixed number of clusters:
```
min_cluster_size=12, min_samples=3, metric='euclidean'
```

**seed_topic_list** — 15 groups of seed keywords representing each constitutional theme. BERTopic embeds these keywords into the same vector space as the sections and uses them to **attract nearby clusters** toward each predefined theme during the clustering phase. This is the **semi-supervised** component: the model still discovers structure from the data, but domain knowledge guides the direction. A section about "ผู้พิพากษา" (judge) clusters with the judicial theme not because the word "ศาล" (court) appears literally, but because WangchanBERTa places them in the same semantic neighborhood.

**Result:** 101 topics mapped to 15 seed themes (or "อื่น ๆ" if no theme match)

### 3.4 Hybrid Soft Scoring

This is the key improvement over attempt 3. Each section passes through one of two scoring paths:

**Path 1 — Keyword Overlap (Primary, 2,406 sections / 87.3%)**

For sections containing at least one token matching any seed lexicon:

```
score(section, theme) = |tokens ∩ seed_keywords(theme)| / |seed_keywords(theme)|
normalized across all themes with score > 0
```

This approach is highly precise for formal constitutional Thai, where domain-specific terms appear consistently — "ศาลรัฐธรรมนูญ" (Constitutional Court) appears only in judicial sections, "คณะรัฐมนตรี" (Cabinet) only in executive sections. The formal, repetitive nature of legal language makes keyword overlap a reliable signal when the vocabulary is present.

**Path 2 — Embedding Cosine Similarity (Fallback, 331 sections / 12.0%)**

For sections with no keyword match across any theme — which would have all become emergent in attempt 3:

1. Compute a **theme centroid** = mean embedding of all sections BERTopic assigned to that theme
2. Compute cosine similarity between the section embedding and all 15 theme centroids
3. Apply **temperature-scaled softmax (T=0.05)** to sharpen the distribution — cosine similarity in high-dimensional space tends to be flat (all values cluster around 0.08–0.10), so temperature scaling amplifies real differences to produce a meaningful peaked distribution
4. Retain only themes where the sharpened score ≥ threshold (tunable parameter)

The theme centroids are derived from BERTopic-assigned documents, making this path a direct extension of the semi-supervised clustering result rather than an independent rule.

**อื่น ๆ (emergent) — 19 sections / 0.7%**

Sections that fail both paths — no keyword evidence and no strong semantic signal toward any theme centroid. These are genuinely anomalous sections that do not belong to any defined theme by either lexical or semantic criteria.

```
Attempt 3 emergent: 352 sections (12.6%)
Attempt 4 emergent:  19 sections  (0.7%)
```

The key outcome of hybrid scoring is that a single section receives **fractional scores across multiple themes simultaneously**, reflecting the reality that constitutional provisions routinely address more than one subject. This multi-theme membership is what distinguishes topic modeling from simple label assignment.

---

## 4. Results

### 4.1 Theme Stability (Cross-Constitutional Coverage)

Stable themes are those that appear consistently across constitutions regardless of era or political regime.

| Theme | Sections | Coverage (of 38) | stable_score |
|-------|----------|------------------|--------------|
| Executive (บริหาร) | 730 | 38/38 (100%) | 0.839 |
| Monarchy (สถาบันพระมหากษัตริย์) | 741 | 36/38 (94.7%) | 0.838 |
| State Policy (แนวนโยบายแห่งรัฐ) | 612 | 36/38 (94.7%) | 0.820 |
| Legislative (นิติบัญญัติ) | 1,257 | 33/38 (86.8%) | 0.779 |
| Political Parties & Elections (พรรคการเมืองและการเลือกตั้ง) | 428 | 28/38 (73.7%) | 0.628 |
| Judiciary (ตุลาการ) | 427 | 22/38 (57.9%) | 0.567 |

The **Executive** theme appears in all 38 constitutions (100%) — the most stable theme across the entire corpus, reflecting that organizing executive power is a non-negotiable element of any constitutional framework regardless of its political orientation.

### 4.2 Theme Dynamics (Temporal Shifts)

Comparing theme mass proportions between early constitutions (percentile 0–35) and late constitutions (percentile 65–100):

| Theme | trend_delta | Direction |
|-------|-------------|-----------|
| Judiciary (ตุลาการ) | +0.052 | Strongest increase |
| Local Government (ท้องถิ่น) | +0.030 | Increasing |
| Anti-Corruption / Oversight (ตรวจสอบอำนาจรัฐ) | +0.017 | Increasing |
| Monarchy (สถาบันพระมหากษัตริย์) | −0.077 | Strongest decrease |
| Political Parties & Elections | −0.020 | Decreasing |
| Legislative (นิติบัญญัติ) | −0.017 | Slight decrease |

Later constitutions place increasing emphasis on **judicial power** and **oversight mechanisms**, reflecting institutional development toward rule of law. The **Monarchy** theme shows a proportional decrease in section count over time — this reflects a shift in constitutional volume rather than a change in institutional importance.

### 4.3 Output Files

| File | Content |
|------|---------|
| `section_theme_scores.csv` | Section-level soft theme scores (fractional, multi-theme) |
| `theme_stable_summary.csv` | Coverage and stability per theme across 38 constitutions |
| `theme_dynamic_summary.csv` | trend_delta comparing early vs. late constitutional periods |
| `theme_timeline_mass.csv` | Theme mass by year for time-series visualization |
| `conflict_edges.csv` | Co-occurrence edges between themes at section level |
| `topic_theme_map.csv` | Mapping from 101 BERTopic topics to 15 seed themes |

---

## 5. Limitations

**1. WangchanBERTa was not pre-trained on legal text**

WangchanBERTa was pre-trained on Thai Common Crawl — general web text — not constitutional or legal corpora. The semantic neighborhoods of domain-specific legal vocabulary may therefore be imprecise. For example, "วรรค" in legal context means paragraph/clause, but in general Thai usage carries different connotations that the model may conflate.

**2. Embedding-based soft scoring has limited effectiveness for Thai constitutional text**

During development, cosine similarity in 768-dimensional space produced very flat distributions — all sections from the same legal domain occupy a tight region of the embedding space, making all theme centroids appear approximately equidistant from any given section. Temperature-scaled softmax was required to amplify real differences, which is a post-hoc correction rather than a natural model output. This is why attempt 4 restricts embedding scoring to a fallback role rather than using it as the primary signal.

**3. Seed themes are researcher-defined**

The 15 themes were designed based on domain knowledge of Thai constitutional structure, not derived purely from the data. The completeness and appropriateness of the taxonomy depends on researcher judgment — a different expert might define different theme boundaries, which would produce different soft scores and coverage statistics.
