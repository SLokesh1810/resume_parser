"""
config.py
=========
Centralised configuration for the resume_parser module.

Edit POPPLER_PATH and TESSERACT_PATH for your OS/environment.
On Linux/macOS both tools are usually on the system PATH, so
leave these as None and the libraries will locate them automatically.
"""

import pytesseract
from pathlib import Path

# ── Directory layout ────────────────────────────────────────────────────────

BASE_DIR: Path = Path(__file__).parent          # .../resume_parser/
RESOURCE_DIR: Path = BASE_DIR / "Resource files"

# ── External tool paths (Windows only) ──────────────────────────────────────
# Set to None on Linux / macOS — the system PATH is used automatically.

POPPLER_PATH: str | None = r"C:\poppler-25.12.0\Library\bin"
TESSERACT_PATH: str | None = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Apply tesseract path if provided
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH