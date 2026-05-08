# Topic Modeling ของมาตราในรัฐธรรมนูญไทย

---

## 1. แรงจูงใจและปัญหา

รัฐธรรมนูญไทย 38 ฉบับ (พ.ศ. 2475–2564) มีโครงสร้างหมวดที่ไม่สอดคล้องกันในแต่ละฉบับ — หมวดเดียวกันอาจมีชื่อต่างกัน หรือเนื้อหาเดียวกันอาจถูกจัดอยู่คนละหมวดในรัฐธรรมนูญต่างฉบับ ดังนั้นการจัดกลุ่มมาตราโดยอาศัย `chapter_title` หรือ `section_title` เพียงอย่างเดียวจึงไม่เพียงพอสำหรับการวิเคราะห์เชิงเปรียบเทียบข้ามฉบับ

วัตถุประสงค์ของส่วนนี้คือการใช้ **topic modeling** เพื่อจัดกลุ่มมาตราตาม **เนื้อหาเชิงความหมาย (semantic content)** โดยไม่ยึดโครงสร้างหมวดเดิม นอกจากนี้ยังต้องการแสดงให้เห็นว่า มาตราหนึ่งสามารถมีส่วนร่วมในหลาย theme พร้อมกันได้ (multi-theme membership) ซึ่งสะท้อนความซับซ้อนของเนื้อหารัฐธรรมนูญที่มักครอบคลุมหลายประเด็นในมาตราเดียว

**Input:** `sections_v2.csv` — 2,797 มาตรา จาก 38 รัฐธรรมนูญ

---

## 2. การพัฒนาวิธีการ

### Attempt 0a — LDA (Latent Dirichlet Allocation)

วิธีแรกที่ทดลองคือ LDA ซึ่งเป็น classic probabilistic topic model โดยใช้ CountVectorizer แปลงข้อความเป็น bag-of-words matrix แล้วให้ LDA หา latent topics

LDA มองข้อความเป็นเพียงการนับความถี่ของคำในแต่ละ document โดยสมมติว่า document หนึ่งประกอบขึ้นจากการ mix หลาย topics และแต่ละ topic คือการกระจายตัว (distribution) ของคำ model จะพยายามหา topics ที่อธิบาย pattern การปรากฏร่วมกันของคำใน corpus ได้ดีที่สุด

**ปัญหา:** LDA ไม่เข้าใจความหมายเชิง semantic — มองแค่ว่าคำไหน co-occur กันบ่อย topic ที่ได้จึงเป็นกลุ่มคำที่มักปรากฏด้วยกัน แต่ไม่สะท้อน constitutional theme ที่ชัดเจน นอกจากนี้ภาษาไทยต้องการ tokenization พิเศษเพื่อแยกคำ ซึ่ง bag-of-words approach ยิ่งทำให้สูญเสีย context มากขึ้น

### Attempt 0b — BERTopic + text-embedding-3-large (OpenRouter)

ปรับมาใช้ BERTopic ซึ่งใช้ dense embeddings แทน bag-of-words พร้อมเพิ่ม visualizations เช่น Intertopic Distance Map และ Hierarchical Topic Tree เพื่อสำรวจโครงสร้างของ topics

**ปัญหา:** embedding model ที่ใช้คือ `text-embedding-3-large` ซึ่งเป็น general-purpose English-first model เมื่อ embed ข้อความภาษาไทย model จะ map คำไทยเข้า vector space ที่ถูก optimize สำหรับภาษาอังกฤษ ทำให้ semantic neighborhood ของคำไทยไม่ถูกต้อง — คำที่มีความหมายใกล้เคียงกันในภาษาไทยอาจอยู่ห่างกันมากใน vector space ส่งผลให้ clustering ไม่สะท้อนความสัมพันธ์เชิงเนื้อหาที่แท้จริง

**บทเรียน:** จำเป็นต้องใช้ embedding model ที่ถูก pre-train บนภาษาไทยโดยเฉพาะ

### Attempt 1 — WangchanBERTa + Unsupervised BERTopic

เปลี่ยนมาใช้ **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`) ซึ่งเป็น BERT-based model ที่ถูก pre-train บน Thai Common Crawl corpus โดยตรง ร่วมกับ BERTopic แบบ unsupervised โดยไม่มี seed guidance และใช้ค่า default parameters ของ BERTopic

**ผลลัพธ์:** พบ 79 topics แต่มีปัญหาสามประการ:
- 617 มาตรา (22.1%) ถูก HDBSCAN จัดเป็น outlier cluster (-1) ไม่ได้รับ topic ใดเลย
- 79 topics มีความละเอียดสูงเกินไป ยากต่อการตีความในระดับ constitutional theme
- BERTopic auto-generated topic names เป็นเพียง top c-TF-IDF keywords เช่น `0_ศาลฎีกา_ผู้ดํารงตําแหน่ง_ไต่สวน_ยื่น` ไม่สามารถใช้ label ข้อมูลได้โดยตรง ต้องอาศัย human interpretation ทุก topic ซึ่ง scale ไม่ได้กับ 79 topics

### Attempt 2 & 3 — Guided BERTopic + Seed Themes

นำ domain knowledge ของโครงสร้างรัฐธรรมนูญไทยมาใช้โดยกำหนด **seed themes** ผ่าน `seed_topic_list` parameter ของ BERTopic — 14 themes ใน attempt 2 และ 15 themes ใน attempt 3 โดยเพิ่ม "พรรคการเมืองและการเลือกตั้ง"

ได้ 101 topics พร้อม soft scoring ระดับมาตรา อย่างไรก็ตาม soft scoring ในสอง attempt นี้ใช้ keyword overlap เป็น heuristic ทำให้มาตราที่ไม่มี seed keyword ปรากฏในข้อความ (352 มาตรา, 12.8%) ถูกจัดเป็น "อื่น ๆ (emergent)" ทั้งหมดโดยไม่คำนึงถึง semantic content

### Attempt 4 — Hybrid Soft Scoring (Final)

แก้ปัญหา emergent สูงด้วย hybrid approach โดยเพิ่ม embedding-based fallback สำหรับมาตราที่ keyword approach ไม่สามารถ assign ได้ (อธิบายละเอียดใน section 3)

**สรุปการพัฒนา:**

| Attempt | วิธีการ | ปัญหาหลัก |
|---------|---------|-----------|
| 0a | LDA + bag-of-words | ไม่เข้าใจ semantic ภาษาไทย |
| 0b | BERTopic + English embedding | Embedding space ไม่เหมาะกับภาษาไทย |
| 1 | WangchanBERTa + unsupervised BERTopic | 79 topics ตีความยาก, 22.1% outlier |
| 2 | Guided BERTopic + 14 seed themes | Soft score เป็น keyword-based เท่านั้น |
| 3 | เพิ่ม theme พรรคการเมืองฯ รวม 15 themes | Emergent ยังสูง 12.8% |
| **4** | **Hybrid soft scoring** | **Emergent ลดเหลือ 0.7%** |

---

## 3. Pipeline รายละเอียด (Attempt 4)

### 3.1 Preprocessing

โหลด `sections_v2.csv` (2,797 มาตรา) แล้ว tokenize ด้วย **AttaCut** ซึ่งเป็น Thai-specific tokenizer ที่ใช้ deep learning model แยกคำภาษาไทยได้แม่นยำกว่า rule-based approaches

จากนั้น filter stopwords 3 กลุ่มที่กำหนดเอง:

**Group A — Function words:** คำที่ทำหน้าที่ทางไวยากรณ์แต่ไม่มีความหมายเชิง topic
```
ตาม, แห่ง, โดย, ซึ่ง, อัน, ใน, แก่, ต่อ, เพื่อ, มิ, ย่อม, ให้, แต่, หรือ, และ, ...
```

**Group B — Document structure noise:** คำที่ปรากฏในทุกมาตราและจะ dominate embedding
```
มาตรา, หมวด, วรรค, ส่วน, บท, รัฐธรรมนูญ, ราชอาณาจักรไทย, พ.ศ., ...
```

**Group C — Legal boilerplate:** คำกฎหมายทั่วไปที่ไม่ distinguish theme
```
กฎหมาย, ระเบียบ, ภายใต้, กรณี, บังคับ, บรรดา, ...
```

Group B มีความสำคัญเป็นพิเศษ — คำว่า "รัฐธรรมนูญ" ปรากฏในทุกมาตรา ถ้าไม่ filter ออก embedding ของทุกมาตราจะถูกดึงไปยังทิศทางเดียวกันใน vector space ทำให้แยกแยะ theme ไม่ได้

หลัง preprocessing: 2,756 มาตรา (41 มาตรา drop เพราะข้อความว่างหลัง filter)

### 3.2 Embedding

แต่ละมาตราถูก embed ด้วย **WangchanBERTa** (`airesearch/wangchanberta-base-att-spm-uncased`)

WangchanBERTa เป็น CamemBERT (RoBERTa-based) architecture ที่ถูก pre-train บน Thai Common Crawl 78GB โดย AIResearch.in.th ใช้ SentencePiece tokenizer ที่ train บน Thai โดยเฉพาะ ทำให้ subword units สะท้อน Thai morphology — ต่างจาก multilingual models ที่แบ่ง capacity กับ 100+ ภาษา model นี้ใช้ 768 dimensions ทั้งหมดสำหรับภาษาไทย

**วิธี embed:**
```
1. ส่ง text เข้า WangchanBERTa tokenizer (max_length=416)
2. รัน forward pass → last_hidden_state shape: (seq_len, 768)
3. Mean pooling: เฉลี่ย token embeddings ที่ไม่ใช่ padding
4. L2 normalization: ทำให้ vector มี magnitude = 1
```

ผลลัพธ์: matrix **2,797 × 768** — แต่ละแถวคือ vector ที่แทนความหมายของมาตรานั้น
```
max_length = 416 tokens
batch_size = 16
device     = MPS (Apple Silicon)
```

### 3.3 Semi-supervised Topic Discovery (Guided BERTopic)

BERTopic ทำงานเป็น orchestrator ที่เรียก 3 components ต่อเนื่อง ทั้งหมดถูกกำหนด parameters เอง:

**ขั้นที่ 1 — UMAP (Dimensionality Reduction)**

ลด embedding จาก 768 → 5 dimensions โดยรักษา local semantic neighborhood
```python
UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine')
```
- `n_neighbors=15` — แต่ละจุดพิจารณา 15 neighbors ใกล้สุดเมื่อสร้าง low-dim representation
- `metric='cosine'` — วัดความคล้ายกันด้วย angle ใน vector space ไม่ใช่ distance

**ขั้นที่ 2 — HDBSCAN (Clustering)**

หา density-based clusters ใน 5D space โดยไม่ต้องกำหนดจำนวน cluster ล่วงหน้า
```python
HDBSCAN(min_cluster_size=12, min_samples=3, metric='euclidean', cluster_selection_method='eom')
```
- `min_cluster_size=12` — cluster ต้องมีอย่างน้อย 12 มาตรา ถ้าน้อยกว่าจะเป็น outlier (-1)
- `min_samples=3` — ความ robust ต่อ noise
- มาตราที่อยู่ในพื้นที่ sparse (ไม่มี neighbors ใกล้พอ) จะได้ topic = -1

**ขั้นที่ 3 — seed_topic_list (Semi-supervised Guidance)**

15 กลุ่มของ seed keywords ที่ represent แต่ละ constitutional theme:
```python
THEME_SEEDS = {
    'สถาบันพระมหากษัตริย์': ['พระมหากษัตริย์', 'สืบราชสมบัติ', 'องคมนตรี', 'ผู้สำเร็จราชการ'],
    'นิติบัญญัติ':           ['รัฐสภา', 'สภาผู้แทนราษฎร', 'วุฒิสภา', 'ตรากฎหมาย'],
    'ตุลาการ':               ['ศาล', 'ศาลยุติธรรม', 'ศาลปกครอง', 'ศาลรัฐธรรมนูญ'],
    ...
}
```

BERTopic embed seed keywords เข้าสู่ vector space เดียวกัน แล้วใช้ตำแหน่งของ seed words เป็น "anchor" เพื่อดึง clusters ที่อยู่ใกล้เคียงให้รวมตัวรอบ theme นั้น — นี่คือ **semi-supervised** component: model ยัง discover structure จากข้อมูลเองผ่าน UMAP + HDBSCAN แต่ domain knowledge ชี้นำทิศทาง

ตัวอย่างที่เห็นได้ชัด: มาตราเกี่ยวกับ "ผู้พิพากษา" cluster กับ theme ตุลาการได้ แม้คำว่า "ผู้พิพากษา" จะไม่อยู่ใน seed list เพราะ WangchanBERTa รู้ว่า "ผู้พิพากษา" และ "ศาล" อยู่ใกล้กันใน semantic space

**ขั้นที่ 4 — c-TF-IDF + Topic→Theme Mapping**

BERTopic สร้าง topic representation ด้วย c-TF-IDF (class-based TF-IDF) ซึ่งหาคำที่ distinctive สำหรับแต่ละ cluster จากนั้น map แต่ละ topic ไปยัง theme โดยนับ seed keywords ที่ปรากฏใน top-15 representative words:

```
topic 0:  ศาลฎีกา ผู้ดํารงตําแหน่ง ไต่สวน ยื่น อัยการ ... → "ศาล" match ตุลาการ → assigned: ตุลาการ
topic 3:  วินิจฉัย คณะตุลาการรัฐธรรมนูญ ร้อง ศาลรัฐธรรมนูญ ... → 2 matches → assigned: ตุลาการ
topic 5:  สนอง พิบูลสงคราม พระบรมราชโองการ ยกเลิก ... → 0 matches → assigned: อื่น ๆ (emergent)
```

**ผลลัพธ์:** 101 topics ถูก map ไปยัง 15 seed themes (หรือ emergent ถ้าไม่มี match)

### 3.4 Hybrid Soft Scoring

นี่คือส่วนที่แตกต่างจาก attempt 3 อย่างมีนัยสำคัญ แต่ละมาตราผ่านการประเมิน 2 paths ตามลำดับ:

```
for each มาตรา:
    คำนวณ keyword overlap กับทุก theme
    │
    ├── มี overlap > 0 → Keyword Path (87.3%)
    │
    └── ไม่มี overlap → Embedding Path (12.0%) หรือ Emergent (0.7%)
```

---

**Path 1 — Keyword Overlap (Primary, 2,406 มาตรา / 87.3%)**

สำหรับมาตราที่มี token ตรงกับ seed lexicon อย่างน้อยหนึ่ง theme:

```
raw_score(theme) = |tokens ∩ seed_keywords(theme)| / |seed_keywords(theme)|
theme_score(theme) = raw_score(theme) / sum(raw_score ทุก theme ที่ > 0)
```

**ตัวอย่างที่ 1 — Single theme**

มาตรา `const_2475_s_2`:
> "อำนาจอธิปไตยย่อมมาจากปวงชนชาวสยาม พระมหากษัตริย์ผู้เป็นประมุข ทรงใช้อำนาจนั้นแต่โดยบทบัญญัติแห่งรัฐธรรมนูญนี้"

```
สถาบันพระมหากษัตริย์ seeds = ['พระมหากษัตริย์','สืบราชสมบัติ','องคมนตรี','ผู้สำเร็จราชการ']
→ "พระมหากษัตริย์" match → raw = 1/4 = 0.25
theme อื่น raw = 0

normalize: 0.25/0.25 = 1.0
```

| section_id | theme | theme_score |
|-----------|-------|-------------|
| const_2475_s_2 | สถาบันพระมหากษัตริย์ | 1.0 |

**ตัวอย่างที่ 2 — Multi theme เท่ากัน**

มาตรา `const_2475_s_6`:
> "พระมหากษัตริย์ทรงใช้อำนาจนิติบัญญัติโดยคำแนะนำและยินยอมของสภาผู้แทนราษฎร"

```
สถาบันพระมหากษัตริย์ → "พระมหากษัตริย์" → raw = 1/4 = 0.25
นิติบัญญัติ → "สภาผู้แทนราษฎร" → raw = 1/4 = 0.25
total = 0.50
```

| section_id | theme | theme_score |
|-----------|-------|-------------|
| const_2475_s_6 | สถาบันพระมหากษัตริย์ | 0.5 |
| const_2475_s_6 | นิติบัญญัติ | 0.5 |

**ตัวอย่างที่ 3 — Multi theme ไม่เท่ากัน**

มาตรา `const_2475_s_7`:
> "พระมหากษัตริย์ทรงใช้อำนาจบริหารทางคณะรัฐมนตรี"

```
สถาบันพระมหากษัตริย์ → "พระมหากษัตริย์" → raw = 1/4 = 0.25
บริหาร seeds = ['คณะรัฐมนตรี','นายกรัฐมนตรี','รัฐมนตรี','บริหาร']
  → "คณะรัฐมนตรี" + "บริหาร" match → raw = 2/4 = 0.50
total = 0.75
```

| section_id | theme | theme_score |
|-----------|-------|-------------|
| const_2475_s_7 | สถาบันพระมหากษัตริย์ | 0.333 |
| const_2475_s_7 | บริหาร | 0.667 |

มาตรานี้พูดถึงบริหารมากกว่ากษัตริย์ — score สะท้อนสัดส่วนนั้น

---

**Path 2 — Embedding Cosine Similarity (Fallback, 331 มาตรา / 12.0%)**

สำหรับมาตราที่ไม่มี keyword match เลย — ซึ่งใน attempt 3 จะกลายเป็น emergent ทั้งหมด

**ขั้นที่ 1 — สร้าง Theme Centroids**
```
theme_centroid(theme) = mean(embeddings ของมาตราทุกมาตราที่ BERTopic assign ให้ theme นั้น)
```
centroid คือจุดศูนย์กลางของ semantic cluster ของ theme นั้น ใน 768-dim space

**ขั้นที่ 2 — Cosine Similarity**
```
sim(section, theme) = cosine_similarity(embedding_section, centroid_theme)
```
ได้ผลลัพธ์ขนาด 2,797 × 15 แต่ค่าที่ได้มักจะ flat เช่น:
```
ตุลาการ: 0.082,  บริหาร: 0.079,  นิติบัญญัติ: 0.081 ...
```
ทุก theme ได้คะแนนใกล้กันมากเพราะข้อความรัฐธรรมนูญทั้งหมดอยู่ใน semantic region เดียวกัน

**ขั้นที่ 3 — Temperature-scaled Softmax (T=0.05)**
```
sharpened(theme) = exp(sim(theme) / 0.05) / Σ exp(sim(all themes) / 0.05)
```
T ที่ต่ำ amplify ความแตกต่างเล็กน้อย ให้กลายเป็นความแตกต่างที่ชัดเจน:
```
ก่อน softmax: ทุก theme ~0.080
หลัง softmax: theme ที่ใกล้สุด >0.40, theme ที่ไกล <0.05
```

**ขั้นที่ 4 — Threshold + Normalize**

เก็บเฉพาะ theme ที่ sharpened score ≥ 0.10 แล้ว normalize ที่เหลือให้รวมเป็น 1.0

**ตัวอย่าง — Embedding path**

มาตรา `const_2475_s_37`:
> "งบประมาณแผ่นดินประจำปี ท่านว่าต้องตราขึ้นเป็นพระราชบัญญัติ..."

"งบประมาณ" ถูก filter ออกใน Group B → ไม่มี keyword match → ไป Path 2

| section_id | theme | theme_score | score_type |
|-----------|-------|-------------|------------|
| const_2475_s_37 | แนวนโยบายแห่งรัฐ | 0.287 | embedding |
| const_2475_s_37 | บริหาร | 0.262 | embedding |
| const_2475_s_37 | สถาบันพระมหากษัตริย์ | 0.226 | embedding |
| const_2475_s_37 | นิติบัญญัติ | 0.226 | embedding |

embedding บอกว่ามาตรานี้ semantically ใกล้กับ แนวนโยบายแห่งรัฐ และ บริหาร ซึ่งสมเหตุสมผลสำหรับมาตราเกี่ยวกับงบประมาณแผ่นดิน

---

**อื่น ๆ (emergent) — 19 มาตรา / 0.7%**

มาตราที่ผ่านทั้ง 2 paths แล้วยัง assign ไม่ได้:
- Path 1: ไม่มี keyword match
- Path 2: ทุก theme มี sharpened score < 0.10

**ตัวอย่าง**

มาตรา `const_2491a_s_1`:
> "รัฐธรรมนูญนี้เรียกว่า รัฐธรรมนูญแห่งราชอาณาจักรไทย (ฉบับชั่วคราว) แก้ไขเพิ่มเติม (ฉบับที่ 2) พ.ศ. 2491"

มาตรานี้เป็นเพียงชื่อเรียกของรัฐธรรมนูญ ไม่มี constitutional content จึงไม่เข้า theme ใด

```
attempt 3 emergent: 352 มาตรา (12.8%)
attempt 4 emergent:  19 มาตรา  (0.7%)
```

**การลดลงนี้มีความหมาย:** emergent ใน attempt 4 คือมาตราที่ genuinely ไม่มีธีม ไม่ใช่ผลจากข้อจำกัดของ keyword list อีกต่อไป

---

**จำนวน theme ต่อมาตรา (attempt 4):**

| จำนวน theme | มาตรา |
|------------|-------|
| 1 | 1,090 |
| 2 | 927 |
| 3 | 512 |
| 4 | 118 |
| 5+ | 90 |

ส่วนใหญ่ได้ 1–2 themes ซึ่งสะท้อนว่า keyword path ให้ผลที่ focused มาตราที่ได้ 3+ themes มักเป็นมาตราที่มีเนื้อหาหลายประเด็นจริง หรืออยู่ใน embedding path ที่ distribution กระจายมากกว่า

---

## 4. ผลลัพธ์

### 4.1 Output Files

| File | เนื้อหา |
|------|---------|
| `section_theme_scores.csv` | Soft theme scores ระดับมาตรา — แต่ละ row คือ (section, theme, score) โดย score รวมต่อ section = 1.0 |
| `theme_stable_summary.csv` | Coverage และ stability ของแต่ละ theme ข้าม 38 รัฐธรรมนูญ |
| `theme_dynamic_summary.csv` | trend_delta เปรียบเทียบยุคต้น (percentile 0–35) กับยุคปลาย (percentile 65–100) |
| `theme_timeline_mass.csv` | Theme mass รวมต่อปี สำหรับ time-series visualization |
| `conflict_edges.csv` | Co-occurrence edges ระหว่าง themes ในระดับมาตรา |
| `topic_theme_map.csv` | Mapping จาก 101 BERTopic topics ไปยัง 15 seed themes |

### 4.2 Theme Stability

**stable_score** คำนวณจาก:
```
stable_score = 0.7 × coverage_ratio + 0.3 × avg_theme_score
```
โดย `coverage_ratio` = สัดส่วนรัฐธรรมนูญที่มี theme นี้ปรากฏ (weight 70%)
และ `avg_theme_score` = คะแนนเฉลี่ยของมาตราใน theme (weight 30%)

| Theme | มาตรา | รัฐธรรมนูญ | coverage | stable_score |
|-------|-------|-----------|---------|-------------|
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

**บริหาร** ปรากฏในรัฐธรรมนูญทุกฉบับ (100%) — เป็น theme ที่ stable ที่สุด สะท้อนว่าการจัดโครงสร้างฝ่ายบริหารเป็นองค์ประกอบพื้นฐานของรัฐธรรมนูญทุกฉบับโดยไม่ขึ้นกับยุคสมัยหรือการเมือง

**ปฏิรูปประเทศ** มีเพียง 2 มาตราใน 2 ฉบับ — สะท้อนว่าเป็น theme ที่เกิดขึ้นเฉพาะในรัฐธรรมนูญยุคหลัง (2560 เป็นต้นไป)

### 4.3 Theme Dynamics

**trend_delta** คำนวณจาก:
```
first_ratio = sum(theme_score ของรัฐธรรมนูญใน percentile 0–35) / total mass ยุคต้น
last_ratio  = sum(theme_score ของรัฐธรรมนูญใน percentile 65–100) / total mass ยุคปลาย
trend_delta = last_ratio − first_ratio
```

ค่าบวก = theme มีสัดส่วนเพิ่มขึ้นในรัฐธรรมนูญยุคหลัง
ค่าลบ = theme มีสัดส่วนลดลงในรัฐธรรมนูญยุคหลัง

| Theme | first_ratio | last_ratio | trend_delta | ทิศทาง |
|-------|------------|-----------|------------|--------|
| ตุลาการ | 6.4% | 11.6% | **+0.052** | เพิ่มมากที่สุด |
| ท้องถิ่น | 1.4% | 4.5% | +0.030 | เพิ่มขึ้น |
| ตรวจสอบอำนาจรัฐ/ต้านทุจริต | 1.0% | 2.8% | +0.017 | เพิ่มขึ้น |
| แนวนโยบายแห่งรัฐ | 10.7% | 11.5% | +0.008 | เพิ่มเล็กน้อย |
| สถาบันพระมหากษัตริย์ | 19.7% | 12.0% | **−0.077** | ลดมากที่สุด |
| พรรคการเมืองและการเลือกตั้ง | 6.9% | 4.9% | −0.020 | ลดลง |
| นิติบัญญัติ | 26.2% | 24.5% | −0.017 | ลดเล็กน้อย |
| บริหาร | 12.6% | 12.6% | −0.000 | คงที่ |

รัฐธรรมนูญยุคหลังให้น้ำหนักกับ **ตุลาการ** และ **กลไกตรวจสอบ** มากขึ้น สะท้อนพัฒนาการของสถาบันทางการเมืองในทิศทางของ rule of law ในขณะที่ **สถาบันพระมหากษัตริย์** มีสัดส่วน section count ลดลงในเชิงปริมาณ — ซึ่งไม่ได้หมายความว่าความสำคัญของสถาบันลดลง แต่สะท้อนว่าเนื้อหาของรัฐธรรมนูญยุคหลังขยายครอบคลุมประเด็นอื่นมากขึ้น

### 4.4 Co-occurrence (Theme ที่ปรากฏร่วมกันในมาตราเดียวกัน)

| source_theme | target_theme | weight (มาตรา) |
|-------------|-------------|---------------|
| นิติบัญญัติ | สถาบันพระมหากษัตริย์ | 117 |
| นิติบัญญัติ | บริหาร | 97 |
| นิติบัญญัติ | พรรคการเมืองและการเลือกตั้ง | 94 |
| สิทธิ-เสรีภาพ-หน้าที่ | แนวนโยบายแห่งรัฐ | 91 |
| บริหาร | สถาบันพระมหากษัตริย์ | 42 |
| ตุลาการ | สิทธิ-เสรีภาพ-หน้าที่ | 36 |
| สถาบันพระมหากษัตริย์ | แนวนโยบายแห่งรัฐ | 34 |
| นิติบัญญัติ | แนวนโยบายแห่งรัฐ | 32 |

**นิติบัญญัติ** มี co-occurrence สูงที่สุดกับ **สถาบันพระมหากษัตริย์** (117 มาตรา) — สะท้อนว่ามาตราเกี่ยวกับ legislative process ในรัฐธรรมนูญไทยมักกล่าวถึงพระราชอำนาจในกระบวนการนิติบัญญัติควบคู่กันเสมอ เช่น การทรงลงพระปรมาภิไธย การยับยั้งร่างกฎหมาย

---

## 5. ข้อจำกัด

**1. WangchanBERTa ไม่ได้ถูก pre-train บน legal text**

WangchanBERTa ถูก pre-train บน Thai Common Crawl (ข้อความทั่วไปจากอินเทอร์เน็ต) ไม่ใช่ภาษากฎหมายรัฐธรรมนูญโดยตรง ทำให้ semantic neighborhood ของคำศัพท์เฉพาะทางกฎหมายอาจไม่ถูกต้องทั้งหมด เช่น "วรรค" ในบริบทกฎหมายหมายถึง paragraph/clause แต่ใน general Thai อาจมี connotation อื่น

**2. Embedding-based soft scoring มีประสิทธิภาพจำกัดสำหรับภาษารัฐธรรมนูญไทย**

ในระหว่างการพัฒนาพบว่า cosine similarity ใน 768-dim space ให้ distribution ที่ flat มาก เนื่องจากข้อความรัฐธรรมนูญทั้ง corpus อยู่ใน semantic region เดียวกัน ทำให้ทุก theme centroid ได้คะแนนใกล้เคียงกันจนแยกแยะไม่ได้ จำเป็นต้องใช้ temperature-scaled softmax เพื่อ sharpen distribution ซึ่งเป็น post-hoc correction ไม่ใช่ผลโดยตรงจาก model — นี่คือเหตุผลที่ attempt 4 ใช้ embedding เฉพาะเป็น fallback ไม่ใช่ primary method

**3. Seed themes เป็น researcher-defined**

15 themes ถูกออกแบบโดยอ้างอิงจาก domain knowledge ของโครงสร้างรัฐธรรมนูญไทยและ chapter structure ที่พบจากการวิเคราะห์ข้อมูลในขั้นตอน EDA ไม่ได้เกิดจาก data-driven process เพียงอย่างเดียว ความครบถ้วนและความเหมาะสมของ taxonomy ขึ้นอยู่กับ judgment ของผู้วิจัย

**4. มาตราที่อ้างอิงมาตราอื่นถูก embed แบบ isolated**

มาตราที่มีเนื้อหาเป็นการอ้างอิง เช่น "ให้นำมาตรา 87 มาใช้บังคับโดยอนุโลม" ถูก embed จากข้อความของตัวเองเท่านั้น โดยไม่รวมเนื้อหาของมาตราที่ถูกอ้างอิง ทำให้ embedding ไม่สะท้อน semantic content ที่แท้จริงของมาตรานั้น มาตราประเภทนี้เป็นส่วนหนึ่งของ 19 มาตราที่ยังเป็น emergent
