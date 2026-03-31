# resume_parser

A Python module that parses PDF resumes into structured JSON. Supports both native text-based PDFs (ATS-friendly) and image-based PDFs (e.g. Canva resumes) via an automatic OCR fallback.

---

## Project Structure

```
project/
├── resume_parser/
│   ├── __init__.py              ← Public API: parse_resume(), hash_resume()
│   ├── config.py                ← Tool paths and directory constants
│   ├── loader.py                ← JSON knowledge-base loader
│   ├── utils.py                 ← Text helpers + hash_resume()
│   ├── parser.py                ← ResumeParser orchestrator class
│   └── extractor/
│       ├── pdf.py               ← PDF text extraction + OCR fallback
│       ├── sections.py          ← Section splitting (text & OCR modes)
│       ├── personal.py          ← Name, phone, email, links
│       ├── skills.py            ← Skills matching
│       ├── education.py         ← Education records
│       ├── experience.py        ← Work experience records
│       ├── projects.py          ← Project records
│       └── certificates.py      ← Standard + non-standard certifications
├── Resource files/
│   ├── SectionHeaders.json
│   ├── Skills.json
│   ├── Education.json
│   ├── JobRoles.json
│   └── Certificates.json
└── run_parser.py                ← Example caller script
```

---

## Requirements

### Python packages

```
pdfplumber
pdf2image
pytesseract
spacy
```

Install them with:

```bash
pip install pdfplumber pdf2image pytesseract spacy
python -m spacy download en_core_web_sm
```

### External tools

| Tool | Purpose | Install |
|---|---|---|
| **Poppler** | PDF → image conversion (OCR path) | See below |
| **Tesseract** | OCR engine | See below |

**Windows**

- Poppler: Download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) and extract anywhere.
- Tesseract: Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).

**Linux**

```bash
sudo apt install poppler-utils tesseract-ocr
```

**macOS**

```bash
brew install poppler tesseract
```

---

## Configuration

Open `resume_parser/config.py` and set your paths:

```python
# Windows — point to actual install locations
POPPLER_PATH  = r"C:\poppler-25.12.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Linux / macOS — leave as None, tools are on the system PATH
POPPLER_PATH  = None
TESSERACT_PATH = None
```

`RESOURCE_DIR` points to the `Resource files/` folder inside the module by default and does not need to be changed unless you move the JSON files.

---

## Usage

### Quickstart

```python
from resume_parser import parse_resume

json_str = parse_resume("Resume.pdf")
print(json_str)
```

`parse_resume()` returns a **JSON string**. To work with it as a Python dict:

```python
import json
from resume_parser import parse_resume

data = json.loads(parse_resume("Resume.pdf"))
print(data["personal_info"]["name"])
print(data["skills"])
```

### Custom paths

If your resource files or Poppler are in non-default locations, pass them explicitly:

```python
from resume_parser import parse_resume

json_str = parse_resume(
    path         = "Resume.pdf",
    resource_dir = r"C:\MyProject\knowledge_base",
    poppler_path = r"C:\poppler\bin",
)
```

### Using the class directly

```python
from resume_parser.parser import ResumeParser

parser = ResumeParser("Resume.pdf")

print(parser)           # pretty-printed JSON string
print(parser.data)      # plain Python dict
print(parser.to_json()) # JSON string (same as str(parser))
```

### Hashing a resume

Before parsing, you can generate a SHA-256 hash of the raw PDF file. This is useful for checking whether a resume has already been processed in your database, avoiding redundant work.

```python
from resume_parser import hash_resume

file_hash = hash_resume("Resume.pdf")
print(file_hash)
# e.g. "a3f1d87c2e..."
```

With a custom algorithm:

```python
file_hash = hash_resume("Resume.pdf", algorithm="md5")
```

### Recommended pattern with a database

```python
import json
from resume_parser import parse_resume, hash_resume

file_hash = hash_resume("Resume.pdf")

if db.exists(file_hash):
    result = db.fetch(file_hash)       # already parsed — skip
else:
    result = json.loads(parse_resume("Resume.pdf"))
    db.save(file_hash, result)
```

### From the command line

```bash
python run_parser.py "Resume.pdf"
```

This prints the SHA-256 hash followed by the full JSON output to stdout.

---

## Output format

`parse_resume()` returns a JSON string with the following top-level keys:

```json
{
    "personal_info": {
        "name":  "Jane Doe",
        "phone": ["9876543210"],
        "mail":  ["jane@example.com"],
        "links": ["https://linkedin.com/in/janedoe"]
    },
    "education": [
        {
            "degree":         "Bachelor of Technology",
            "level":          "Undergraduate",
            "specialization": "Computer science",
            "institution":    "Anna university",
            "duration":       "2020 - 2024",
            "score":          "8.5 / 10"
        }
    ],
    "skills": ["Django", "Docker", "PostgreSQL", "Python", "React"],
    "experience": [
        {
            "role":        "Software Engineer",
            "category":    "Engineering",
            "company":     "Acme Corp",
            "duration":    "Jan 2024 - Present",
            "description": "..."
        }
    ],
    "projects": [
        {
            "title":       "Resume Parser",
            "tech_stack":  ["FastAPI", "Python", "spaCy"],
            "links":       ["https://github.com/user/resume-parser"],
            "description": "..."
        }
    ],
    "certifications": {
        "standard": [
            {
                "name":   "AWS Certified Developer",
                "issuer": "Amazon Web Services",
                "type":   "standard"
            }
        ],
        "non_standard": [
            {
                "name":   "coursera machine learning specialization",
                "issuer": "Coursera",
                "type":   "non-standard"
            }
        ]
    }
}
```

---

## How it works

1. **PDF extraction** — `extractor/pdf.py` first attempts text-based extraction with `pdfplumber`. It then runs four quality checks (personal info, sections, skills, education/experience). If two or more checks fail, it falls back to OCR using `pdf2image` + `pytesseract`.

2. **Section splitting** — `extractor/sections.py` detects section headers by matching aliases from `SectionHeaders.json` and slices the text into a dict of named sections.

3. **Field extraction** — Each extractor module receives only its relevant section text and matches against its knowledge-base JSON, using regex patterns for structured fields like dates, scores, and company names.

4. **Output** — The `ResumeParser` class assembles all results into a dict; `to_json()` serialises it.

---

## Knowledge-base JSON format

All five JSON files follow the same schema — a list of objects with a canonical name and a list of aliases for matching:

```json
[
    {
        "canonical": "Python",
        "aliases": ["python", "python3", "py"]
    }
]
```

`Education.json` and `JobRoles.json` have extra fields:

```json
[
    {
        "canonical": "Bachelor of Technology",
        "aliases": ["b.tech", "be", "b.e"],
        "level": "undergraduate",
        "specializations": ["computer science", "information technology"]
    }
]
```

To support a new skill, degree, or job role, simply add an entry to the relevant JSON file — no code changes needed.

---

## Adding a new extractor

1. Create `resume_parser/extractor/your_field.py` with a single pure function:
   ```python
   def extract_your_field(text: str, db: list[dict]) -> list:
       ...
   ```
2. Load the knowledge-base JSON in `loader.py` under a new key.
3. Call it in `parser.py` inside `_parse_resume()` and add the result to the returned dict.
4. Export it from `__init__.py` if callers need it directly.