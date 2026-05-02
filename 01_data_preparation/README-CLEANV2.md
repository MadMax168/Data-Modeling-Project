# Thai Constitution Post-Processor v2

Post-processor สำหรับแปลง raw OCR JSON ของรัฐธรรมนูญไทย  
ให้เป็น **Structured JSON** และ **CSV** ที่พร้อมใช้วิเคราะห์

---

## Quick Start

```bash
# ติดตั้ง (ไม่ต้องติดตั้ง library เพิ่ม ใช้ Python stdlib)
python --version  # ต้องการ Python 3.10+

# Process ไฟล์เดียว
python constitution_postprocessor_v2.py --input const_2475.json

# Process ทั้งโฟลเดอร์พร้อมกัน (batch)
python constitution_postprocessor_v2.py --input ./raw/ --batch

# กำหนด output folder
python constitution_postprocessor_v2.py --input ./raw/ --batch --output ./structured/
```

---

## Input ที่รองรับ

Script รองรับ JSON 2 รูปแบบ:

| รูปแบบ | คำอธิบาย | Field ที่ใช้ |
|---|---|---|
| **Raw OCR JSON** | Output จาก pipeline OCR ของเพื่อน | `full_text` หรือ `pages[].raw_markdown` |
| **Structured v1 JSON** | Output จาก postprocessor v1 | `chapters[].sections` (reconstruct ก่อน re-parse) |

> **แนะนำ:** ใช้กับ raw OCR JSON จะได้ผลดีที่สุด เพราะ v1 อาจตัด section ผิดไปแล้ว

---

## Output Files

รัน 1 ไฟล์ได้ 2 output, รัน batch ได้เพิ่ม 1 ไฟล์รวม:

```
structured_output/
├── structured_2475.json       ← Nested JSON (1 ไฟล์ต่อฉบับ)
├── sections_2475.csv          ← Flat CSV   (1 ไฟล์ต่อฉบับ)
├── structured_2492.json
├── sections_2492.csv
└── all_sections_combined.csv  ← รวมทุกฉบับ (batch เท่านั้น)
```

---

## โครงสร้าง JSON (`structured_YYYY.json`)

### ภาพรวม

```
{
  metadata (id, year, era, ...)
  preamble
  summary { total_chapters, total_parts, total_sections }
  chapters [
    {
      chapter metadata
      parts [          ← มีเฉพาะหมวดที่มี "ส่วนที่"
        {
          part metadata
          sections [ { section_number, text } ]
        }
      ]
      sections [       ← มาตราที่ไม่อยู่ใน "ส่วนที่"
        { section_number, text }
      ]
    }
  ]
}
```

### อธิบายแต่ละ Field

#### ระดับ Root

| Field | Type | ตัวอย่าง | คำอธิบาย |
|---|---|---|---|
| `id` | string | `"const_2475"` | unique ID ของฉบับ |
| `year_th` | int | `2475` | ปี พ.ศ. |
| `year_ce` | int | `1932` | ปี ค.ศ. |
| `name_short` | string | `"Constitution 2475"` | ชื่อย่อ |
| `constitution_type` | string | `"original"` / `"amendment"` | ประเภทฉบับ: ฉบับใหม่หรือฉบับแก้ไข |
| `amends_year` | int \| null | `2475` / `null` | ถ้าเป็น amendment → ปีของฉบับที่ถูกแก้ไข |
| `source_type` | string | `"image_pdf"` | ต้นทางของ PDF |
| `processing_method` | string | `"typhoon-ocr-0.4.1"` | OCR engine ที่ใช้ |
| `era` | string | `"early_democracy"` | ยุคสมัย |
| `regime_type` | string | `"civilian"` / `"military"` | ประเภทรัฐบาล |
| `preamble` | string | `"...คำปรารภ..."` | คำปรารภของรัฐธรรมนูญ (≤2000 chars) |

#### `summary`

| Field | Type | คำอธิบาย |
|---|---|---|
| `total_pages` | int | จำนวนหน้า PDF |
| `total_chapters` | int | จำนวนหมวดทั้งหมด |
| `total_parts` | int | จำนวนส่วนทั้งหมด (0 ถ้าไม่มี "ส่วนที่") |
| `total_sections` | int | จำนวนมาตราทั้งหมด |
| `total_chars` | int | จำนวนตัวอักษรหลัง clean |

#### `chapters[]`

| Field | Type | ตัวอย่าง | คำอธิบาย |
|---|---|---|---|
| `chapter_number` | int | `1`, `0`, `-1` | เลขหมวด (0 = บททั่วไป, -1 = บทเฉพาะกาล/บทสุดท้าย) |
| `chapter_title` | string | `"พระมหากษัตริย์"` | ชื่อหมวด |
| `section_count` | int | `31` | จำนวนมาตราในหมวดนี้ทั้งหมด (รวมที่อยู่ใน ส่วน) |
| `parts` | array | `[...]` | ส่วนที่ภายในหมวด (ว่างถ้าหมวดไม่มี "ส่วนที่") |
| `sections` | array | `[...]` | มาตราที่ไม่ได้อยู่ใน ส่วน |

#### `chapters[].parts[]`

| Field | Type | ตัวอย่าง | คำอธิบาย |
|---|---|---|---|
| `part_number` | int | `1` | เลขส่วน |
| `part_title` | string | `"ส่วนที่ 1 วุฒิสภา"` | ชื่อส่วน (เต็ม) |
| `section_count` | int | `15` | จำนวนมาตราในส่วนนี้ |
| `sections` | array | `[...]` | มาตราในส่วนนี้ |

#### `chapters[].sections[]` และ `parts[].sections[]`

| Field | Type | ตัวอย่าง | คำอธิบาย |
|---|---|---|---|
| `section_number` | int | `3` | เลขมาตรา (arabic integer) |
| `text` | string | `"องค์พระมหากษัตริย์..."` | เนื้อหามาตรา (cleaned, normalized) |

### ตัวอย่าง JSON เต็ม

```json
{
  "id": "const_2475",
  "year_th": 2475,
  "year_ce": 1932,
  "name_short": "Constitution 2475",
  "constitution_type": "original",
  "amends_year": null,
  "era": "early_democracy",
  "regime_type": "civilian",
  "preamble": "สมเด็จพระปรมินทรมหาประชาธิปก...",
  "summary": {
    "total_pages": 23,
    "total_chapters": 7,
    "total_parts": 0,
    "total_sections": 68,
    "total_chars": 18500
  },
  "chapters": [
    {
      "chapter_number": 0,
      "chapter_title": "บททั่วไป",
      "section_count": 2,
      "parts": [],
      "sections": [
        { "section_number": 1, "text": "สยามประเทศเป็นราชอาณาจักรอันหนึ่งอันเดียว จะแบ่งแยกมิได้" },
        { "section_number": 2, "text": "อำนาจอธิปไตยย่อมมาจากปวงชนชาวสยาม..." }
      ]
    },
    {
      "chapter_number": 6,
      "chapter_title": "อำนาจนิติบัญญัติ",
      "section_count": 72,
      "parts": [
        {
          "part_number": 1,
          "part_title": "ส่วนที่ 1 วุฒิสภา",
          "section_count": 15,
          "sections": [
            { "section_number": 82, "text": "วุฒิสภาประกอบด้วยสมาชิกมีจำนวนหนึ่งร้อยคน..." }
          ]
        },
        {
          "part_number": 2,
          "part_title": "ส่วนที่ 2 สภาผู้แทน",
          "section_count": 20,
          "sections": [
            { "section_number": 97, "text": "สภาผู้แทนประกอบด้วยสมาชิก..." }
          ]
        }
      ],
      "sections": [
        { "section_number": 73, "text": "รัฐสภาประกอบด้วยวุฒิสภาและสภาผู้แทน..." }
      ]
    }
  ]
}
```

---

## โครงสร้าง CSV

### `sections_YYYY.csv` (per-constitution)

1 row = 1 มาตรา เรียงตาม `section_number`

| Column | Type | ตัวอย่าง | คำอธิบาย |
|---|---|---|---|
| `constitution_id` | string | `const_2475` | unique ID |
| `year_th` | int | `2475` | ปี พ.ศ. |
| `year_ce` | int | `1932` | ปี ค.ศ. |
| `name_short` | string | `Constitution 2475` | ชื่อย่อ |
| `constitution_type` | string | `original` | `original` หรือ `amendment` |
| `amends_year` | int \| empty | `2475` | ปีฉบับที่ถูกแก้ไข (ถ้าเป็น amendment) |
| `era` | string | `early_democracy` | ยุคสมัย |
| `regime_type` | string | `civilian` | ประเภทรัฐบาล |
| `chapter_number` | int | `1` | เลขหมวด |
| `chapter_title` | string | `พระมหากษัตริย์` | ชื่อหมวด |
| `part_number` | int \| empty | `2` | เลขส่วน (ว่างถ้าไม่มี ส่วนที่) |
| `part_title` | string \| empty | `ส่วนที่ 2 สภาผู้แทน` | ชื่อส่วน (ว่างถ้าไม่มี ส่วนที่) |
| `section_number` | int | `3` | เลขมาตรา |
| `section_text` | string | `องค์พระมหากษัตริย์...` | เนื้อหามาตรา |

### `all_sections_combined.csv` (batch เท่านั้น)

Schema เดียวกับ `sections_YYYY.csv` แต่รวมทุกฉบับไว้ด้วยกัน เรียงตาม `year_th` → `section_number`  
ใช้สำหรับ cross-version analysis เปรียบเทียบข้ามฉบับ

---

## ตัวอย่างการใช้งาน CSV ด้วย pandas

```python
import pandas as pd

df = pd.read_csv("all_sections_combined.csv")

# ดูมาตรา 1 จากทุกฉบับ — เปรียบเทียบ text ข้ามปี
df[df["section_number"] == 1][["year_th", "section_text"]]

# ดูหมวดพระมหากษัตริย์ทุกฉบับ
df[df["chapter_title"].str.contains("พระมหากษัตริย์")]

# นับจำนวนมาตราแต่ละฉบับ
df.groupby("year_th")["section_number"].count()

# หาฉบับที่เป็น amendment ทั้งหมด
df[df["constitution_type"] == "amendment"][["year_th", "amends_year"]].drop_duplicates()

# เปรียบเทียบหมวดและส่วนของรัฐธรรมนูญปี 2492
df_2492 = df[df["year_th"] == 2492]
df_2492.groupby(["chapter_title", "part_title"])["section_number"].count()
```

---

## สิ่งที่ v2 แก้ไขจาก v1

| ปัญหา | สาเหตุ | วิธีแก้ใน v2 |
|---|---|---|
| **Bunch ไม่คม** — sub-items `(1)(2)(3)` หลุดออกจากมาตรา | `.*?` non-greedy regex ตัด boundary ผิด | เปลี่ยนเป็น position-based split |
| **มาตราเดียวกันถูกตัดเป็นหลาย row** — เช่น มาตรา 90 เป็น 5 records | OCR inline header แทรกกลาง text ทำให้ตัดผิด | `_merge_cross_chapter_duplicates()` รวม section เลขเดียวกัน |
| **"ส่วนที่" ไม่รู้จัก** — sections ทั้งหมดของหมวดหลุดไป chapter อื่น | Parser รู้จักแค่ หมวด/มาตรา | เพิ่ม `_RE_PART` เป็น level กลาง, CSV มี `part_number` + `part_title` |
| **ประกาศแก้ไข ref กลับไม่ได้** | ไม่มี field แยก original vs amendment | เพิ่ม `constitution_type` และ `amends_year` |

---

## หมายเหตุ

- Script ใช้ Python stdlib เท่านั้น (`re`, `json`, `csv`, `pathlib`) ไม่ต้อง `pip install` เพิ่ม
- Encoding ของ CSV เป็น **UTF-8 with BOM** (`utf-8-sig`) เพื่อให้เปิดใน Excel ได้ถูกต้อง
- `chapter_number = 0` หมายถึง **บททั่วไป** หรือ **บทนำ**
- `chapter_number = -1` หมายถึง **บทเฉพาะกาล**, **บทสุดท้าย**, หรือ **บทเบ็ดเตล็ด**
- ถ้า `part_number` และ `part_title` ว่างใน CSV แปลว่ามาตรานั้นอยู่ใต้หมวดโดยตรง (ไม่มีส่วนคั่น)