# บทที่ 5 การจำแนกหัวข้อด้วย Topic Modeling

หลังจากผ่านกระบวนการเตรียมข้อมูลและวิเคราะห์เชิงสำรวจในบทที่ 3 และ 4 แล้ว ผู้จัดทำได้นำข้อมูลมาตราจาก `sections_v2.csv` มาผ่านกระบวนการ **Topic Modeling** เพื่อจัดกลุ่มมาตราตามเนื้อหาเชิงความหมาย (Semantic Content) โดยไม่ยึดโครงสร้างหมวดเดิมที่ไม่สอดคล้องกันระหว่างฉบับ

---

## 5.1 ที่มาและปัญหา

รัฐธรรมนูญไทย 38 ฉบับ (พ.ศ. 2475–2564) มีโครงสร้างหมวดที่ไม่สอดคล้องกันในแต่ละฉบับ — หมวดเดียวกันอาจมีชื่อต่างกัน หรือเนื้อหาเดียวกันอาจถูกจัดอยู่คนละหมวดในรัฐธรรมนูญต่างฉบับ ดังนั้นการจัดกลุ่มมาตราโดยอาศัย `chapter_title` หรือ `section_title` เพียงอย่างเดียวจึงไม่เพียงพอสำหรับการวิเคราะห์เชิงเปรียบเทียบข้ามฉบับ

วัตถุประสงค์ของส่วนนี้คือการใช้ **Topic Modeling** เพื่อจัดกลุ่มมาตราตามเนื้อหาเชิงความหมาย (Semantic Content) โดยไม่ยึดโครงสร้างหมวดเดิม นอกจากนี้ยังต้องการแสดงให้เห็นว่ามาตราหนึ่งสามารถมีส่วนร่วมในหลาย theme พร้อมกันได้ (Multi-theme Membership) ซึ่งสะท้อนความซับซ้อนของเนื้อหารัฐธรรมนูญที่มักครอบคลุมหลายประเด็นในมาตราเดียว

**Input:** `sections_v2.csv` — 2,797 มาตรา จาก 38 รัฐธรรมนูญ

---

## 5.2 การพัฒนาวิธีการ (Methodology Progression)

ผู้จัดทำได้ทดลองวิธีการหลายแนวทางก่อนจะได้ pipeline สุดท้าย โดยแต่ละ attempt ได้ข้อเรียนรู้ที่นำไปสู่การปรับปรุงในขั้นต่อไป

### Attempt 0a — LDA (Latent Dirichlet Allocation)

วิธีแรกที่ทดลองคือ LDA ซึ่งเป็น Classic Probabilistic Topic Model โดยใช้ CountVectorizer แปลงข้อความเป็น Bag-of-Words Matrix แล้วให้ LDA ค้นหา Latent Topics

LDA มองข้อความเป็นเพียงการนับความถี่ของคำใน Document โดยสมมติว่า Document หนึ่งประกอบขึ้นจากการผสม (mix) หลาย Topics และแต่ละ Topic คือการกระจายตัว (Distribution) ของคำ โมเดลจะพยายามหา Topics ที่อธิบาย pattern การปรากฏร่วมกันของคำใน Corpus ได้ดีที่สุด

**ปัญหา:** LDA ไม่เข้าใจความหมายเชิง Semantic — มองแค่ว่าคำไหน Co-occur กันบ่อย Topic ที่ได้จึงเป็นกลุ่มคำที่มักปรากฏด้วยกัน แต่ไม่สะท้อน Constitutional Theme ที่ชัดเจน นอกจากนี้ภาษาไทยต้องการ Tokenization พิเศษเพื่อแยกคำ ซึ่ง Bag-of-Words Approach ยิ่งทำให้สูญเสีย Context มากขึ้น

### Attempt 0b — BERTopic + text-embedding-3-large (OpenRouter)

ปรับมาใช้ BERTopic ซึ่งใช้ Dense Embeddings แทน Bag-of-Words พร้อมเพิ่ม Visualizations เช่น Intertopic Distance Map และ Hierarchical Topic Tree เพื่อสำรวจโครงสร้างของ Topics

**ปัญหา:** Embedding Model ที่ใช้คือ `text-embedding-3-large` ซึ่งเป็น General-purpose English-first Model เมื่อ Embed ข้อความภาษาไทย โมเดลจะ Map คำไทยเข้า Vector Space ที่ถูก Optimize สำหรับภาษาอังกฤษ ทำให้ Semantic Neighborhood ของคำไทยไม่ถูกต้อง — คำที่มีความหมายใกล้เคียงกันในภาษาไทยอาจอยู่ห่างกันมากใน Vector Space ส่งผลให้ Clustering ไม่สะท้อนความสัมพันธ์เชิงเนื้อหาที่แท้จริง

**บทเรียน:** จำเป็นต้องใช้ Embedding Model ที่ถูก Pre-train บนภาษาไทยโดยเฉพาะ

### Attempt 1 — WangchanBERTa + Unsupervised BERTopic

เปลี่ยนมาใช้ **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`) ซึ่งเป็น BERT-based Model ที่ถูก Pre-train บน Thai Common Crawl Corpus โดยตรง ร่วมกับ BERTopic แบบ Unsupervised โดยไม่มี Seed Guidance

**ผลลัพธ์:** พบ 79 Topics แต่มีปัญหาสามประการ:
- 617 มาตรา (22.1%) ถูก HDBSCAN จัดเป็น Outlier Cluster (-1) ไม่ได้รับ Topic ใดเลย
- 79 Topics มีความละเอียดสูงเกินไป ยากต่อการตีความในระดับ Constitutional Theme
- BERTopic Auto-generated Topic Names เป็นเพียง Top c-TF-IDF Keywords เช่น `0_ศาลฎีกา_ผู้ดํารงตําแหน่ง_ไต่สวน_ยื่น` ซึ่งต้องอาศัย Human Interpretation ทุก Topic และ Scale ไม่ได้กับ 79 Topics

### Attempt 2 & 3 — Guided BERTopic + Seed Themes

นำ Domain Knowledge ของโครงสร้างรัฐธรรมนูญไทยมาใช้โดยกำหนด **Seed Themes** ผ่าน `seed_topic_list` Parameter ของ BERTopic — 14 Themes ใน Attempt 2 และ 15 Themes ใน Attempt 3 โดยเพิ่ม "พรรคการเมืองและการเลือกตั้ง"

ได้ 101 Topics พร้อม Soft Scoring ระดับมาตรา อย่างไรก็ตาม Soft Scoring ในสอง Attempt นี้ใช้ Keyword Overlap เป็น Heuristic ทำให้มาตราที่ไม่มี Seed Keyword ปรากฏในข้อความ (352 มาตรา, 12.8%) ถูกจัดเป็น "อื่น ๆ (emergent)" ทั้งหมดโดยไม่คำนึงถึง Semantic Content

### Attempt 4 — Hybrid Soft Scoring (Final)

แก้ปัญหา Emergent Rate สูงด้วย Hybrid Approach โดยเพิ่ม Embedding-based Fallback สำหรับมาตราที่ Keyword Approach ไม่สามารถ Assign ได้ (อธิบายละเอียดใน 5.3)

ตาราง 11 สรุปการพัฒนา Methodology ใน 5 Attempts

| Attempt | วิธีการ | ปัญหาหลัก |
|---------|---------|-----------|
| 0a | LDA + Bag-of-Words | ไม่เข้าใจ Semantic ภาษาไทย |
| 0b | BERTopic + English Embedding | Embedding Space ไม่เหมาะกับภาษาไทย |
| 1 | WangchanBERTa + Unsupervised BERTopic | 79 Topics ตีความยาก, 22.1% Outlier |
| 2 | Guided BERTopic + 14 Seed Themes | Soft Score เป็น Keyword-based เท่านั้น |
| 3 | เพิ่ม Theme พรรคการเมืองฯ รวม 15 Themes | Emergent ยังสูง 12.8% |
| **4** | **Hybrid Soft Scoring** | **Emergent ลดเหลือ 0.7%** |

---

## 5.3 รายละเอียด Pipeline (Attempt 4)

### 5.3.1 Preprocessing

โหลด `sections_v2.csv` (2,797 มาตรา) แล้ว Tokenize ด้วย **AttaCut** ซึ่งเป็น Thai-specific Tokenizer ที่ใช้ Deep Learning Model แยกคำภาษาไทยได้แม่นยำกว่า Rule-based Approaches

จากนั้น Filter Stopwords 3 กลุ่มที่กำหนดเอง:

- **Group A — Function Words:** คำที่ทำหน้าที่ทางไวยากรณ์แต่ไม่มีความหมายเชิง Topic เช่น ตาม, แห่ง, โดย, ซึ่ง, อัน, ใน, แก่, ต่อ, เพื่อ
- **Group B — Document Structure Noise:** คำที่ปรากฏในทุกมาตราและจะ Dominate Embedding เช่น มาตรา, หมวด, วรรค, ส่วน, บท, รัฐธรรมนูญ, ราชอาณาจักรไทย
- **Group C — Legal Boilerplate:** คำกฎหมายทั่วไปที่ไม่ Distinguish Theme เช่น กฎหมาย, ระเบียบ, ภายใต้, กรณี, บังคับ, บรรดา

Group B มีความสำคัญเป็นพิเศษ — คำว่า "รัฐธรรมนูญ" ปรากฏในทุกมาตรา ถ้าไม่ Filter ออก Embedding ของทุกมาตราจะถูกดึงไปยังทิศทางเดียวกันใน Vector Space ทำให้แยกแยะ Theme ไม่ได้

หลัง Preprocessing: 2,756 มาตรา (41 มาตราถูก Drop เพราะข้อความว่างหลัง Filter)

### 5.3.2 Embedding

แต่ละมาตราถูก Embed ด้วย **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`) ซึ่งเป็น CamemBERT (RoBERTa-based) Architecture ที่ถูก Pre-train บน Thai Common Crawl 78GB โดย AIResearch.in.th ใช้ SentencePiece Tokenizer ที่ Train บนภาษาไทยโดยเฉพาะ — ต่างจาก Multilingual Models ที่แบ่ง Capacity กับ 100+ ภาษา โมเดลนี้ใช้ 768 Dimensions ทั้งหมดสำหรับภาษาไทย

วิธี Embed: ส่ง Text เข้า WangchanBERTa Tokenizer (max_length=416) → รัน Forward Pass → Last Hidden State → Mean Pooling (เฉลี่ย Token Embeddings ที่ไม่ใช่ Padding) → L2 Normalization

ผลลัพธ์: Matrix **2,797 × 768** — แต่ละแถวคือ Vector ที่แทนความหมายของมาตรานั้น

```
max_length = 416 tokens
batch_size = 16
device     = MPS (Apple Silicon)
```

### 5.3.3 Semi-supervised Topic Discovery (Guided BERTopic)

BERTopic ทำงานเป็น Orchestrator ที่เรียก 3 Components ต่อเนื่อง ทั้งหมดถูกกำหนด Parameters เอง:

**ขั้นที่ 1 — UMAP (Dimensionality Reduction)**

ลด Embedding จาก 768 → 5 Dimensions โดยรักษา Local Semantic Neighborhood
```
UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine')
```
- `n_neighbors=15` — แต่ละจุดพิจารณา 15 Neighbors ใกล้สุดเมื่อสร้าง Low-dimensional Representation
- `metric='cosine'` — วัดความคล้ายกันด้วย Angle ใน Vector Space ไม่ใช่ Distance

**ขั้นที่ 2 — HDBSCAN (Clustering)**

หา Density-based Clusters ใน 5D Space โดยไม่ต้องกำหนดจำนวน Cluster ล่วงหน้า
```
HDBSCAN(min_cluster_size=12, min_samples=3, metric='euclidean')
```
- `min_cluster_size=12` — Cluster ต้องมีอย่างน้อย 12 มาตรา ถ้าน้อยกว่าจะเป็น Outlier (-1)
- `min_samples=3` — ความ Robust ต่อ Noise

**ขั้นที่ 3 — seed_topic_list (Semi-supervised Guidance)**

15 กลุ่มของ Seed Keywords ที่ Represent แต่ละ Constitutional Theme ถูกส่งเข้า BERTopic ผ่าน `seed_topic_list` Parameter BERTopic จะ Embed Seed Keywords เข้าสู่ Vector Space เดียวกัน แล้วใช้ตำแหน่งของ Seed Words เป็น "Anchor" เพื่อดึง Clusters ที่อยู่ใกล้เคียงให้รวมตัวรอบ Theme นั้น

ตัวอย่างที่เห็นได้ชัด: มาตราเกี่ยวกับ "ผู้พิพากษา" Cluster กับ Theme ตุลาการได้ แม้คำว่า "ผู้พิพากษา" จะไม่อยู่ใน Seed List เพราะ WangchanBERTa รู้ว่า "ผู้พิพากษา" และ "ศาล" อยู่ใกล้กันใน Semantic Space

**ผลลัพธ์:** 101 Topics ถูก Map ไปยัง 15 Seed Themes (หรือ "อื่น ๆ" ถ้าไม่มี Match)

### 5.3.4 Hybrid Soft Scoring

นี่คือส่วนที่แตกต่างจาก Attempt 3 อย่างมีนัยสำคัญ แต่ละมาตราผ่านการประเมิน 2 Paths ตามลำดับ:

**Path 1 — Keyword Overlap (Primary, 2,406 มาตรา / 87.3%)**

สำหรับมาตราที่มี Token ตรงกับ Seed Lexicon อย่างน้อยหนึ่ง Theme:

```
raw_score(theme) = |tokens ∩ seed_keywords(theme)| / |seed_keywords(theme)|
theme_score(theme) = raw_score(theme) / sum(raw_score ทุก theme ที่ > 0)
```

วิธีนี้ให้ความแม่นยำสูงสำหรับภาษากฎหมายรัฐธรรมนูญ เนื่องจากคำศัพท์เฉพาะทางปรากฏอย่างสม่ำเสมอ — เช่น "ศาลรัฐธรรมนูญ" ปรากฏเฉพาะในมาตราตุลาการ และ "คณะรัฐมนตรี" ปรากฏเฉพาะในมาตราบริหาร

**Path 2 — Embedding Cosine Similarity (Fallback, 331 มาตรา / 12.0%)**

สำหรับมาตราที่ไม่มี Keyword Match เลย — ซึ่งใน Attempt 3 จะกลายเป็น Emergent ทั้งหมด:

1. คำนวณ **Theme Centroid** = Mean Embedding ของมาตราทุกมาตราที่ BERTopic Assign ให้ Theme นั้น
2. คำนวณ Cosine Similarity ระหว่าง Section Embedding กับ Theme Centroids ทั้ง 15 Themes
3. ใช้ **Temperature-scaled Softmax (T=0.05)** เพื่อ Sharpen Distribution เนื่องจาก Cosine Similarity ใน High-dimensional Space มักจะ Flat (ทุกค่าอยู่ในช่วง 0.08–0.10)
4. เก็บเฉพาะ Theme ที่ Sharpened Score ≥ Threshold แล้ว Normalize ที่เหลือให้รวมเป็น 1.0

**อื่น ๆ (Emergent) — 19 มาตรา / 0.7%**

มาตราที่ผ่านทั้ง 2 Paths แล้วยัง Assign ไม่ได้ — ไม่มี Keyword Evidence และไม่มี Semantic Signal ที่แข็งแกร่งต่อ Theme Centroid ใดเลย มาตราเหล่านี้เป็นมาตราที่ไม่มีเนื้อหาเชิง Constitutional อย่างแท้จริง เช่น มาตราที่ระบุเพียงชื่อเรียกของรัฐธรรมนูญ หรือมาตราที่อ้างอิงมาตราอื่นโดยไม่มีเนื้อหาในตัวเอง

ตาราง 12 เปรียบเทียบ Emergent Rate ระหว่าง Attempt 3 และ Attempt 4

| | Attempt 3 | Attempt 4 |
|---|---|---|
| Emergent (อื่น ๆ) | 352 มาตรา (12.8%) | 19 มาตรา (0.7%) |
| Keyword Path | 2,406 มาตรา (87.3%) | 2,406 มาตรา (87.3%) |
| Embedding Fallback | — | 331 มาตรา (12.0%) |

ผลสำคัญของ Hybrid Scoring คือมาตราหนึ่งจะได้รับ **Fractional Scores ข้าม Theme พร้อมกัน** สะท้อนความจริงที่ว่ามาตรารัฐธรรมนูญมักครอบคลุมหลายประเด็นในมาตราเดียว ดังที่แสดงในตาราง 13

ตาราง 13 การกระจายตัวของจำนวน Theme ต่อมาตรา (Attempt 4)

| จำนวน Theme ต่อมาตรา | จำนวนมาตรา |
|---------------------|-----------|
| 1 | 1,090 |
| 2 | 927 |
| 3 | 512 |
| 4 | 118 |
| 5 ขึ้นไป | 90 |

---

## 5.4 ผลลัพธ์

### 5.4.1 ไฟล์ Output

ตาราง 14 ไฟล์ Output จาก Topic Modeling Pipeline (Attempt 4)

| ไฟล์ | เนื้อหา |
|------|---------|
| `section_theme_scores.csv` | Soft Theme Scores ระดับมาตรา — แต่ละ Row คือ (section, theme, score) โดย Score รวมต่อ Section = 1.0 |
| `theme_stable_summary.csv` | Coverage และ Stability ของแต่ละ Theme ข้าม 38 รัฐธรรมนูญ |
| `theme_dynamic_summary.csv` | Trend Delta เปรียบเทียบยุคต้น (Percentile 0–35) กับยุคปลาย (Percentile 65–100) |
| `theme_timeline_mass.csv` | Theme Mass รวมต่อปี สำหรับ Time-series Visualization |
| `conflict_edges.csv` | Co-occurrence Edges ระหว่าง Themes ในระดับมาตรา |
| `topic_theme_map.csv` | Mapping จาก 101 BERTopic Topics ไปยัง 15 Seed Themes |

### 5.4.2 ความเสถียรของ Theme (Theme Stability)

**stable_score** คำนวณจาก:
```
stable_score = 0.7 × coverage_ratio + 0.3 × avg_theme_score
```
โดย `coverage_ratio` คือสัดส่วนรัฐธรรมนูญที่มี Theme นี้ปรากฏ (Weight 70%) และ `avg_theme_score` คือคะแนนเฉลี่ยของมาตราใน Theme (Weight 30%)

ตาราง 15 สรุป Theme Stability ทั้ง 15 Themes

| Theme | จำนวนมาตรา | รัฐธรรมนูญ | Coverage | stable_score |
|-------|-----------|-----------|---------|-------------|
| บริหาร | 730 | 38/38 | 100.0% | 0.839 |
| สถาบันพระมหากษัตริย์ | 741 | 36/38 | 94.7% | 0.838 |
| แนวนโยบายแห่งรัฐ | 612 | 36/38 | 94.7% | 0.820 |
| นิติบัญญัติ | 1,257 | 33/38 | 86.8% | 0.779 |
| พรรคการเมืองและการเลือกตั้ง | 428 | 28/38 | 73.7% | 0.628 |
| สิทธิ-เสรีภาพ-หน้าที่ | 662 | 25/38 | 65.8% | 0.598 |
| ตุลาการ | 427 | 22/38 | 57.9% | 0.567 |
| ท้องถิ่น | 178 | 15/38 | 39.5% | 0.406 |
| จริยธรรมทางการเมือง | 98 | 13/38 | 34.2% | 0.373 |
| การคลังและงบประมาณ | 91 | 14/38 | 36.8% | 0.365 |
| ตรวจสอบอำนาจรัฐ/ต้านทุจริต | 137 | 14/38 | 36.8% | 0.352 |
| ทั่วไป/โครงสร้าง | 31 | 10/38 | 26.3% | 0.311 |
| การมีส่วนร่วมทางการเมือง | 46 | 10/38 | 26.3% | 0.289 |
| องค์กรอิสระ/องค์กรตามรัฐธรรมนูญ | 19 | 7/38 | 18.4% | 0.249 |
| ปฏิรูปประเทศ | 2 | 2/38 | 5.3% | 0.337 |

**Theme บริหาร** ปรากฏในรัฐธรรมนูญทุกฉบับ (100%) — เป็น Theme ที่ Stable ที่สุด สะท้อนว่าการจัดโครงสร้างฝ่ายบริหารเป็นองค์ประกอบพื้นฐานของรัฐธรรมนูญทุกฉบับโดยไม่ขึ้นกับยุคสมัยหรือระบอบการเมือง

**Theme ปฏิรูปประเทศ** มีเพียง 2 มาตราใน 2 ฉบับ — สะท้อนว่าเป็น Theme ที่เกิดขึ้นเฉพาะในรัฐธรรมนูญยุคหลัง (พ.ศ. 2560 เป็นต้นไป)

รูปที่ 5.4.1 แสดง Heatmap สัดส่วนมาตราของแต่ละ Theme ต่อรัฐธรรมนูญแต่ละฉบับ

### 5.4.3 พลวัตของ Theme (Theme Dynamics)

**trend_delta** คำนวณจากการเปรียบเทียบสัดส่วน Theme Mass ระหว่างยุคต้น (Percentile 0–35) กับยุคปลาย (Percentile 65–100):

```
trend_delta = last_ratio − first_ratio
```

ค่าบวก หมายความว่า Theme มีสัดส่วนเพิ่มขึ้นในรัฐธรรมนูญยุคหลัง
ค่าลบ หมายความว่า Theme มีสัดส่วนลดลงในรัฐธรรมนูญยุคหลัง

ตาราง 16 สรุป Theme Dynamics (เฉพาะ Theme ที่มีการเปลี่ยนแปลงชัดเจน)

| Theme | first_ratio | last_ratio | trend_delta | ทิศทาง |
|-------|------------|-----------|------------|--------|
| ตุลาการ | 6.4% | 11.6% | +0.052 | เพิ่มมากที่สุด |
| ท้องถิ่น | 1.4% | 4.5% | +0.030 | เพิ่มขึ้น |
| ตรวจสอบอำนาจรัฐ/ต้านทุจริต | 1.0% | 2.8% | +0.017 | เพิ่มขึ้น |
| แนวนโยบายแห่งรัฐ | 10.7% | 11.5% | +0.008 | เพิ่มเล็กน้อย |
| บริหาร | 12.6% | 12.6% | −0.000 | คงที่ |
| นิติบัญญัติ | 26.2% | 24.5% | −0.017 | ลดเล็กน้อย |
| พรรคการเมืองและการเลือกตั้ง | 6.9% | 4.9% | −0.020 | ลดลง |
| สถาบันพระมหากษัตริย์ | 19.7% | 12.0% | −0.077 | ลดมากที่สุด |

รัฐธรรมนูญยุคหลังให้น้ำหนักกับ **Theme ตุลาการ** และ **กลไกตรวจสอบ** มากขึ้น สะท้อนพัฒนาการของสถาบันทางการเมืองในทิศทางของ Rule of Law ในขณะที่ **Theme สถาบันพระมหากษัตริย์** มีสัดส่วน Section Count ลดลงในเชิงปริมาณ — ซึ่งไม่ได้หมายความว่าความสำคัญของสถาบันลดลง แต่สะท้อนว่าเนื้อหาของรัฐธรรมนูญยุคหลังขยายครอบคลุมประเด็นอื่น ๆ เพิ่มมากขึ้น

รูปที่ 5.4.2 แสดงสัดส่วนของแต่ละ Theme ต่อรัฐธรรมนูญแต่ละฉบับ แสดงให้เห็นพลวัตเชิงเวลาข้าง Constitutions ทั้ง 38 ฉบับ

### 5.4.4 Co-occurrence ระหว่าง Theme

ตาราง 17 Theme Co-occurrence ที่พบบ่อยที่สุด (จำนวนมาตราที่มีทั้งสอง Theme พร้อมกัน)

| Theme A | Theme B | จำนวนมาตรา |
|---------|---------|-----------|
| นิติบัญญัติ | สถาบันพระมหากษัตริย์ | 117 |
| นิติบัญญัติ | บริหาร | 97 |
| นิติบัญญัติ | พรรคการเมืองและการเลือกตั้ง | 94 |
| สิทธิ-เสรีภาพ-หน้าที่ | แนวนโยบายแห่งรัฐ | 91 |
| บริหาร | สถาบันพระมหากษัตริย์ | 42 |
| ตุลาการ | สิทธิ-เสรีภาพ-หน้าที่ | 36 |
| สถาบันพระมหากษัตริย์ | แนวนโยบายแห่งรัฐ | 34 |
| นิติบัญญัติ | แนวนโยบายแห่งรัฐ | 32 |

**Theme นิติบัญญัติ** มี Co-occurrence สูงที่สุดกับ **สถาบันพระมหากษัตริย์** (117 มาตรา) — สะท้อนว่ามาตราเกี่ยวกับ Legislative Process ในรัฐธรรมนูญไทยมักกล่าวถึงพระราชอำนาจในกระบวนการนิติบัญญัติควบคู่กันเสมอ เช่น การทรงลงพระปรมาภิไธย การยับยั้งร่างกฎหมาย

---

## 5.5 ข้อจำกัด

**1. WangchanBERTa ไม่ได้ถูก Pre-train บน Legal Text**

WangchanBERTa ถูก Pre-train บน Thai Common Crawl (ข้อความทั่วไปจากอินเทอร์เน็ต) ไม่ใช่ภาษากฎหมายรัฐธรรมนูญโดยตรง ทำให้ Semantic Neighborhood ของคำศัพท์เฉพาะทางกฎหมายอาจไม่ถูกต้องทั้งหมด เช่น "วรรค" ในบริบทกฎหมายหมายถึง Paragraph หรือ Clause แต่ใน General Thai อาจมี Connotation อื่น

**2. Embedding-based Soft Scoring มีประสิทธิภาพจำกัดสำหรับภาษารัฐธรรมนูญไทย**

ในระหว่างการพัฒนาพบว่า Cosine Similarity ใน 768-dimensional Space ให้ Distribution ที่ Flat มาก เนื่องจากข้อความรัฐธรรมนูญทั้ง Corpus อยู่ใน Semantic Region เดียวกัน ทำให้ทุก Theme Centroid ได้คะแนนใกล้เคียงกันจนแยกแยะไม่ได้ จำเป็นต้องใช้ Temperature-scaled Softmax เพื่อ Sharpen Distribution ซึ่งเป็น Post-hoc Correction ไม่ใช่ผลโดยตรงจากโมเดล — นี่คือเหตุผลที่ Attempt 4 ใช้ Embedding เฉพาะเป็น Fallback ไม่ใช่ Primary Method

**3. Seed Themes เป็น Researcher-defined**

15 Themes ถูกออกแบบโดยอ้างอิงจาก Domain Knowledge ของโครงสร้างรัฐธรรมนูญไทยและ Chapter Structure ที่พบจากการวิเคราะห์ข้อมูลในขั้นตอน EDA ไม่ได้เกิดจาก Data-driven Process เพียงอย่างเดียว ความครบถ้วนและความเหมาะสมของ Taxonomy ขึ้นอยู่กับ Judgment ของผู้วิจัย — นักวิจัยคนอื่นอาจกำหนด Theme Boundaries ต่างออกไป ซึ่งจะให้ Soft Scores และ Coverage Statistics ที่แตกต่างกัน

**4. มาตราที่อ้างอิงมาตราอื่นถูก Embed แบบ Isolated**

มาตราที่มีเนื้อหาเป็นการอ้างอิง เช่น "ให้นำมาตรา 87 มาใช้บังคับโดยอนุโลม" ถูก Embed จากข้อความของตัวเองเท่านั้น โดยไม่รวมเนื้อหาของมาตราที่ถูกอ้างอิง ทำให้ Embedding ไม่สะท้อน Semantic Content ที่แท้จริงของมาตรานั้น มาตราประเภทนี้เป็นส่วนหนึ่งของ 19 มาตราที่ยังเป็น Emergent
