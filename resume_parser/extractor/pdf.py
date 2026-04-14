"""
extractor/pdf.py
================
Handles low-level PDF reading.

Two strategies:
  1. Text-based  – uses pdfplumber (fast, accurate for ATS / digital resumes).
  2. OCR-based   – converts pages to images via pdf2image then runs Tesseract
                   (slower, needed for scanned / Canva-style resumes).

The public entry-point `extract_pdf` automatically decides which strategy to
use based on how well the text-based extraction performs.
"""

import re
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

def extract_images_and_design(pdf_path):

    image_count = 0
    pages_with_images = 0
    low_text_pages = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Count images
            if page.images:
                image_count += len(page.images)
                pages_with_images += 1

            # Text density
            words = page.extract_words()
            if len(words) < 40:
                low_text_pages += 1

    return {
        "image_count": image_count,
        "pages_with_images": pages_with_images,
        "low_text_pages": low_text_pages,
        "total_pages": len(pdf.pages)
    }

# ── Low-level readers ────────────────────────────────────────────────────────
def extract_text_from_pdf(pdf_path) -> tuple[str, str]:
    """
    Extract text from a native (text-layer) PDF using pdfplumber.

    Words are grouped into lines by comparing their vertical position so that
    multi-column layouts are handled gracefully.

    Returns:
        (text, 'text') — raw extracted text and a type-tag.
    """
    lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=True)

            line: list[str] = []
            prev_top = None

            for w in words:
                if prev_top is None or abs(w["top"] - prev_top) < 3:
                    line.append(w["text"])
                else:
                    lines.append(" ".join(line))
                    line = [w["text"]]
                prev_top = w["top"]

            if line:
                lines.append(" ".join(line))

    return "\n".join(lines), "text"

def extract_text_with_ocr(images) -> tuple[str, str]:
    """
    Convert each PDF page to an image and run Tesseract OCR on it.

    Args:
        pdf_path     (str | Path): Path to the PDF file.
        poppler_path (str | None): Poppler binary directory (Windows only).

    Returns:
        (text, 'ocr') — OCR text and a type-tag.
    """
    text = ""

    for img in images:
        text += pytesseract.image_to_string(img) + "\n"

    return text, "ocr"


# ── Smart dispatcher ─────────────────────────────────────────────────────────
def extract_pdf(pdf_path, poppler_path=None, extractors: dict = None):
    """
    Try text-based extraction first; fall back to OCR if quality is poor.

    Quality is judged by running four lightweight checks on the text-based
    output.  If two or more checks fail the OCR path is taken.

    Args:
        pdf_path     (str | Path): Path to the PDF.
        poppler_path (str | None): Poppler path for OCR fallback.
        extractors   (dict)      : Optional dict of callable extractors used
                                   for the quality checks.  Expected keys:
                                   "personal_info", "sections", "skills",
                                   "education", "experience".

    Returns:
        (text, type_tag) where type_tag is 'text' or 'ocr'.
    """
    text, _ = extract_text_from_pdf(pdf_path)
    cleaned = re.sub(r"\s+", " ", text).strip()

    failed_checks = 0

    if extractors:
        sections   = extractors["sections"](cleaned)
        skills     = extractors["skills"](sections.get("skills", cleaned))
        education  = extractors["education"](sections.get("education", ""))
        experience = extractors["experience"](sections.get("experience", ""))

        if not sections:
            failed_checks += 1
        if not skills:
            failed_checks += 1
        if not education and not experience:
            failed_checks += 1
    else:
        if len(cleaned) < 100:
            failed_checks = 2

    kwargs = {"poppler_path": poppler_path} if poppler_path else {}
    images = convert_from_path(pdf_path, **kwargs)
    design_details = extract_images_and_design(pdf_path)

    #  TEXT PATH
    if failed_checks < 2:
        return text, "text", design_details

    #  OCR PATH
    print("[INFO] Weak text extraction → OCR fallback")
    ocr_text, _ = extract_text_with_ocr(images)

    return ocr_text, "ocr", design_details