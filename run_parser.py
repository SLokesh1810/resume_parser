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
from pathlib import Path

# ── Optional: only needed on Windows when Poppler is not on the system PATH ──
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"   # set to None on Linux/macOS
RESOURCE_DIR = Path("resume_parser") / "Resource files"


def main():
    if len(sys.argv) < 2:
        print('Usage: python run_parser.py "path/to/resume.pdf"')
        sys.exit(1)

    resume_path = sys.argv[1]

    from resume_parser import parse_resume, hash_resume

    # ── Hash first (cheap) ────────────────────────────────────────────────────
    file_hash = hash_resume(resume_path)
    print(f"[INFO] Resume hash (sha256): {file_hash}")

    # TODO: check file_hash against your database here before parsing

    # ── Parse and get JSON ────────────────────────────────────────────────────
    print(f"[INFO] Parsing: {resume_path}")
    json_str = parse_resume(
        path         = resume_path,
        resource_dir = RESOURCE_DIR,
        poppler_path = POPPLER_PATH,
    )

    # ── Print JSON to stdout ──────────────────────────────────────────────────
    print(json_str)


if __name__ == "__main__":
    main()