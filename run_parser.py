"""
run_parser.py
=============
Example script that calls the resume_parser module from outside its folder.

Place this file one level above the resume_parser/ directory:

    project/
    ├── resume_parser/          ← the module
    └── run_parser.py           ← this file

Run:
    python run_parser.py "path/to/resume.pdf"
"""

import sys
import json
from pathlib import Path
from resume_parser import parse_resume, hash_resume
from resume_scoring import scorer

POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
RESOURCE_DIR = Path("resume_parser") / "Resource files"


def main():
    if len(sys.argv) < 2:
        print('Usage: python run_parser.py "path/to/resume.pdf"')
        sys.exit(1)

    resume_path = sys.argv[1]

    # ── Hash ────────────────────────────────────────────────────
    file_hash = hash_resume(resume_path)
    print(f"[INFO] Resume hash (sha256): {file_hash}")

    # ── Parse ───────────────────────────────────────────────────
    print(f"[INFO] Parsing: {resume_path}")

    json_str = parse_resume(
        path=resume_path,
        resource_dir=RESOURCE_DIR,
        poppler_path=POPPLER_PATH,
    )

    data = json.loads(json_str)
    text = data.get('text', "")
    resume_type = data.get('resume_type', '')
    design_details = data.get('design_details', '')
    data = dict(data)
    data.pop('text', None)
    data.pop('resume_type', None)
    data.pop('design_details', None)

    print(json.dumps(data, indent=4))

    score = scorer.resume_score(text, data, resume_type, design_details)
    print(json.dumps(score, indent=4))


if __name__ == "__main__":
    main()