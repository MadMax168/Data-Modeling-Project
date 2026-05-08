# Topic Modeling of Thai Constitutional Sections

## 1. แรงจูงใจและปัญหา (Motivation)

รัฐธรรมนูญไทย 38 ฉบับ (พ.ศ. 2475–2564) มีโครงสร้างหมวดที่ไม่สอดคล้องกันในแต่ละฉบับ — หมวดเดียวกันอาจมีชื่อต่างกัน หรือเนื้อหาเดียวกันอาจถูกจัดอยู่คนละหมวดในรัฐธรรมนูญต่างฉบับ ดังนั้นการจัดกลุ่มมาตราโดยอาศัย `chapter_title` หรือ `section_title` เพียงอย่างเดียวจึงไม่เพียงพอสำหรับการวิเคราะห์เชิงเปรียบเทียบข้ามฉบับ

วัตถุประสงค์ของส่วนนี้คือการใช้ **topic modeling** เพื่อจัดกลุ่มมาตราตาม **เนื้อหาเชิงความหมาย** (semantic content) โดยไม่ยึดโครงสร้างหมวดเดิม นอกจากนี้ยังต้องการแสดงให้เห็นว่า มาตราหนึ่งสามารถมีส่วนร่วมในหลาย theme พร้อมกันได้ (multi-theme membership) ซึ่งสะท้อนความซับซ้อนของเนื้อหารัฐธรรมนูญที่มักครอบคลุมหลายประเด็นในมาตราเดียว

**Input:** `sections_v2.csv` — 2,797 มาตรา จาก 38 รัฐธรรมนูญ

---

## 2. การพัฒนาวิธีการ (Methodology Progression)

### Attempt 0a — LDA (Latent Dirichlet Allocation)

วิธีแรกที่ทดลองคือ LDA ซึ่งเป็น classic probabilistic topic model โดยใช้ CountVectorizer แปลงข้อความเป็น bag-of-words matrix แล้วให้ LDA หา latent topics

**ปัญหา:** LDA มองข้อความเป็นเพียงการนับความถี่ของคำ ไม่เข้าใจความหมายเชิง semantic ทำให้ topic ที่ได้เป็นกลุ่มคำที่ co-occur กันบ่อย แต่ไม่สะท้อนธีมรัฐธรรมนูญที่ชัดเจน นอกจากนี้ภาษาไทยซึ่งต้องการ tokenization พิเศษทำให้ bag-of-words approach ยิ่งสูญเสีย context มากขึ้น

### Attempt 0b — BERTopic + text-embedding-3-large (OpenRouter)

ปรับมาใช้ BERTopic ซึ่งใช้ embeddings แทน bag-of-words พร้อม visualizations เพิ่มเติมเช่น Intertopic Distance Map และ Hierarchical Topic Tree เพื่อสำรวจโครงสร้างของ topics

**ปัญหา:** model ที่ใช้คือ `text-embedding-3-large` ซึ่งเป็น general-purpose English-first embedding model เมื่อนำมา embed ข้อความภาษาไทย model จะ map คำไทยเข้า embedding space ที่ถูก optimize สำหรับภาษาอังกฤษ ทำให้ semantic neighborhood ของคำไทยไม่ถูกต้อง — คำที่มีความหมายใกล้เคียงในภาษาไทยอาจอยู่ห่างกันใน vector space จึงทำให้ clustering ไม่สะท้อนความสัมพันธ์เชิงเนื้อหาที่แท้จริง

**บทเรียน:** จำเป็นต้องใช้ embedding model ที่ถูก pre-train บนภาษาไทยโดยเฉพาะ

### Attempt 1 — WangchanBERTa + Unsupervised BERTopic

เปลี่ยนมาใช้ **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`) ซึ่งเป็น BERT-based model ที่ถูก pre-train บน Thai Common Crawl corpus โดยตรง ร่วมกับ BERTopic แบบ unsupervised (ไม่มี seed guidance)

**ผลลัพธ์:** พบ 79 topics (ไม่นับ outlier -1) แต่มีปัญหาสองประการ:
- มาตรา 617 มาตรา (22.1%) ถูก HDBSCAN จัดเป็น outlier (-1) ไม่ได้อยู่ใน topic ใดเลย
- 79 topics มีความละเอียดสูงเกินไป ยากต่อการตีความในระดับ theme

### Attempt 2 & 3 — Guided BERTopic + Seed Themes

นำ domain knowledge ของโครงสร้างรัฐธรรมนูญไทยมาใช้โดยกำหนด **seed themes** 14 themes (attempt 2) และ 15 themes (attempt 3 เพิ่ม "พรรคการเมืองและการเลือกตั้ง") ผ่าน `seed_topic_list` parameter ของ BERTopic

ได้ 101 topics พร้อม soft scoring ระดับมาตรา อย่างไรก็ตาม soft scoring ใน attempt นี้ใช้ keyword overlap เป็น heuristic ทำให้มาตราที่ไม่มี seed keyword ปรากฏในข้อความ (352 มาตรา, 12.8%) ถูกจัดเป็น "อื่น ๆ (emergent)" ทั้งหมด

### Attempt 4 — Hybrid Soft Scoring (Final)

แก้ปัญหา emergent ที่สูงเกินไปด้วย hybrid approach โดยเพิ่ม embedding-based fallback สำหรับมาตราที่ keyword approach ไม่สามารถ assign ได้ (อธิบายละเอียดใน section 3)

---

## 3. Pipeline รายละเอียด (Attempt 4)

### 3.1 Preprocessing

โหลด `sections_v2.csv` แล้ว tokenize ด้วย **AttaCut** (Thai-specific tokenizer) จากนั้น filter stopwords 3 กลุ่ม:

- **Group A** — function words (ใน, โดย, ซึ่ง, เพื่อ, ...)
- **Group B** — document structure noise (มาตรา, หมวด, วรรค, รัฐธรรมนูญ, ...)
- **Group C** — legal boilerplate (กฎหมาย, ระเบียบ, ภายใต้, ...)

การ filter Group B มีความสำคัญเป็นพิเศษ — คำว่า "รัฐธรรมนูญ" ปรากฏในทุกมาตราทำให้ถ้าไม่ filter จะ dominate embedding และทำให้ทุกมาตราดูเหมือนกันใน vector space

### 3.2 Embedding

แต่ละมาตราถูก embed ด้วย **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`) ด้วย mean-pooling บน last hidden state และ L2 normalization ได้ผลลัพธ์เป็น matrix ขนาด **2,797 × 768** โดยแต่ละแถวคือ vector ที่แทนความหมายของมาตรานั้นใน embedding space

```
max_length = 416 tokens
batch_size = 16
device     = MPS (Apple Silicon)
```

### 3.3 Semi-supervised Topic Discovery (Guided BERTopic)

BERTopic ทำงาน 3 ขั้นตอนต่อเนื่องโดยใช้ component ที่กำหนดเอง:

**UMAP** — ลด dimension จาก 768 → 5 โดยรักษา semantic neighborhood:
```
n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine'
```

**HDBSCAN** — หา clusters จาก 5D space โดยไม่บังคับจำนวน cluster:
```
min_cluster_size=12, min_samples=3, metric='euclidean'
```

**seed_topic_list** — 15 กลุ่มของ seed keywords ที่ represent แต่ละ constitutional theme ถูก embed เข้าสู่ vector space เดียวกัน และใช้ดึง (attract) clusters ที่อยู่ใกล้เคียงให้รวมตัวรอบ theme นั้น นี่คือ **semi-supervised** component — model ยังคง discover patterns จากข้อมูลเอง แต่มี domain knowledge ชี้นำทิศทาง

**ผลลัพธ์:** 101 topics ที่ถูก map ไปยัง 15 seed themes (หรือ "อื่น ๆ" ถ้าไม่ match)

### 3.4 Hybrid Soft Scoring

นี่คือส่วนที่แตกต่างจาก attempt 3 อย่างมีนัยสำคัญ แต่ละมาตราผ่าน 2 paths:

**Path 1 — Keyword (Primary, 2,406 มาตรา / 87.3%)**

สำหรับมาตราที่มี token ตรงกับ seed lexicon อย่างน้อยหนึ่ง theme:

```
score(section, theme) = |tokens ∩ seed_keywords(theme)| / |seed_keywords(theme)|
normalized across all themes with score > 0
```

วิธีนี้ให้ความแม่นยำสูงสำหรับภาษารัฐธรรมนูญที่เป็น formal และ repetitive เช่น "ศาลรัฐธรรมนูญ" ปรากฏใน judicial sections เท่านั้น

**Path 2 — Embedding Cosine Similarity (Fallback, 331 มาตรา / 12.0%)**

สำหรับมาตราที่ไม่มี keyword match เลย (เดิมจะถูกจัดเป็น emergent ทั้งหมดใน attempt 3):

1. คำนวณ **theme centroid** = ค่าเฉลี่ย embedding ของมาตราทั้งหมดที่ BERTopic assign ให้ theme นั้น
2. คำนวณ cosine similarity ระหว่าง section embedding กับ centroid ทั้ง 15 themes
3. Apply **temperature-scaled softmax (T=0.05)** เพื่อ sharpen distribution — แปลงค่าที่ flat ใน high-dimensional space ให้มี peak ที่ชัดเจน
4. เก็บเฉพาะ themes ที่ sharpened score ≥ threshold (tunable)

Theme centroid มาจาก BERTopic-assigned documents จึงทำให้ path นี้เชื่อมต่อกับผล semi-supervised clustering โดยตรง

**อื่น ๆ (emergent) — 19 มาตรา / 0.7%**

มาตราที่ผ่านทั้ง 2 paths แล้วยัง assign ไม่ได้ — genuinely ไม่เข้า theme ใดทั้งในเชิง lexical และ semantic

```
attempt 3 emergent: 352 มาตรา (12.6%)
attempt 4 emergent:  19 มาตรา  (0.7%)
```

**ผลลัพธ์หลักของ hybrid scoring** คือมาตราหนึ่งสามารถมีคะแนนใน **หลาย theme พร้อมกัน** (fractional membership) สะท้อนความจริงที่ว่ามาตรารัฐธรรมนูญมักครอบคลุมหลายประเด็น

---

## 4. ผลลัพธ์ (Outputs)

### 4.1 Theme Stability (ความคงทนข้ามรัฐธรรมนูญ)

| Theme | มาตราที่เกี่ยวข้อง | coverage (จาก 38 ฉบับ) | stable_score |
|-------|-------------------|------------------------|--------------|
| บริหาร | 730 | 38/38 (100%) | 0.839 |
| สถาบันพระมหากษัตริย์ | 741 | 36/38 (94.7%) | 0.838 |
| แนวนโยบายแห่งรัฐ | 612 | 36/38 (94.7%) | 0.820 |
| นิติบัญญัติ | 1,257 | 33/38 (86.8%) | 0.779 |
| พรรคการเมืองและการเลือกตั้ง | 428 | 28/38 (73.7%) | 0.628 |
| ตุลาการ | 427 | 22/38 (57.9%) | 0.567 |

**บริหาร** ปรากฏในรัฐธรรมนูญทุกฉบับ (100%) — เป็น theme ที่ stable ที่สุด สะท้อนว่าการจัดโครงสร้างฝ่ายบริหารเป็นองค์ประกอบพื้นฐานที่ขาดไม่ได้

### 4.2 Theme Dynamics (การเปลี่ยนแปลงตามช่วงเวลา)

เปรียบเทียบสัดส่วน theme mass ระหว่างรัฐธรรมนูญยุคต้น (percentile 0–35) กับยุคปลาย (percentile 65–100):

| Theme | trend_delta | ทิศทาง |
|-------|-------------|--------|
| ตุลาการ | +0.052 | เพิ่มขึ้นมากที่สุด |
| ท้องถิ่น | +0.030 | เพิ่มขึ้น |
| ตรวจสอบอำนาจรัฐ/ต้านทุจริต | +0.017 | เพิ่มขึ้น |
| สถาบันพระมหากษัตริย์ | −0.077 | ลดลงมากที่สุด |
| พรรคการเมืองและการเลือกตั้ง | −0.020 | ลดลง |
| นิติบัญญัติ | −0.017 | ลดลงเล็กน้อย |

รัฐธรรมนูญยุคหลังให้น้ำหนักกับ **ตุลาการ** และ **กลไกตรวจสอบ** มากขึ้น สะท้อนการพัฒนาสถาบันทางการเมืองในทิศทางของ rule of law ในขณะที่ **สถาบันพระมหากษัตริย์** มีสัดส่วนลดลงในเชิงปริมาณ (ไม่ได้หมายความว่าความสำคัญลดลง)

### 4.3 Output Files

| File | เนื้อหา |
|------|---------|
| `section_theme_scores.csv` | soft theme scores ระดับมาตรา (fractional, multi-theme) |
| `theme_stable_summary.csv` | coverage และ stability ของแต่ละ theme ข้าม 38 ฉบับ |
| `theme_dynamic_summary.csv` | trend_delta เปรียบเทียบยุคต้นกับยุคปลาย |
| `theme_timeline_mass.csv` | theme mass ตาม year_th สำหรับ time-series visualization |
| `conflict_edges.csv` | co-occurrence edges ระหว่าง themes ระดับมาตรา |
| `topic_theme_map.csv` | mapping จาก 101 BERTopic topics ไปยัง 15 seed themes |

---

## 5. ข้อจำกัด (Limitations)

**1. WangchanBERTa ไม่ได้ถูก pre-train บน legal text**

WangchanBERTa ถูก pre-train บน Thai Common Crawl (ข้อความทั่วไปจากอินเทอร์เน็ต) ไม่ใช่ภาษากฎหมายรัฐธรรมนูญโดยตรง ทำให้ semantic neighborhood ของคำศัพท์เฉพาะทางกฎหมายอาจไม่ถูกต้องทั้งหมด เช่น "วรรค" ในบริบทกฎหมายหมายถึง paragraph แต่ใน general Thai อาจมี connotation อื่น

**2. Embedding-based soft scoring ทำงานได้จำกัดสำหรับภาษารัฐธรรมนูญไทย**

ในระหว่างการพัฒนา พบว่า cosine similarity ใน high-dimensional space (768 dims) ให้ distribution ที่ flat มาก — มาตรา domain เดียวกันทั้งหมดอยู่ใกล้กันใน embedding space ทำให้ทุก theme centroid ได้คะแนนใกล้เคียงกัน จำเป็นต้องใช้ temperature-scaled softmax เพื่อ sharpen distribution ซึ่งเป็น post-hoc correction ไม่ใช่ผลจาก model โดยตรง นี่คือเหตุผลที่ attempt 4 ใช้ embedding เฉพาะเป็น fallback ไม่ใช่ primary scoring method

**3. Seed themes เป็น researcher-defined**

15 themes ถูกออกแบบโดยอ้างอิงจาก domain knowledge ของโครงสร้างรัฐธรรมนูญไทย ไม่ได้เกิดจาก data-driven process เพียงอย่างเดียว ความครบถ้วนและความเหมาะสมของ taxonomy ขึ้นอยู่กับ judgment ของผู้วิจัย
