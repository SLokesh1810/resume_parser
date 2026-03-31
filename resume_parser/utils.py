"""
utils.py
========
Shared text-cleaning and normalisation helpers used across extractor modules.
"""

import re
import hashlib


def clean_text(text: str) -> str:
    """
    Remove non-breaking spaces, bullet-point control characters, and
    collapse all consecutive whitespace into a single space.
    """
    text = text.replace("\xa0", " ")   # non-breaking space
    text = text.replace("\uf0b7", " ") # common bullet-point glyph
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_lines(text: str) -> list[str]:
    """
    Split *text* on newlines, strip each line, and drop blank lines.

    Returns:
        list[str]: Non-empty, stripped lines.
    """
    return [line.strip() for line in text.split("\n") if line.strip()]


def normalize_text(text: str) -> str:
    """
    Lowercase and lightly normalise *text* for fuzzy matching:
      - Collapse whitespace around '.' and '-'
      - Replace '|' with a space
      - Convert to lowercase

    Returns empty string if *text* is falsy.
    """
    if not text:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = re.sub(r"\. ", ".", text)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*-\s*", "-", text)

    return text.lower().strip()


def hash_resume(pdf_path: str, algorithm: str = "sha256") -> str:
    """
    Generate a hash of the raw PDF file bytes.

    The hash is computed directly from the file contents (not the parsed text),
    so two byte-identical PDFs will always produce the same hash regardless of
    how the parser interprets them. Use this to detect duplicate submissions
    before running the full parsing pipeline.

    Intended future use::

        file_hash = hash_resume("resume.pdf")
        if db.exists(file_hash):
            return db.fetch(file_hash)   # skip re-parsing
        else:
            result = parse_resume("resume.pdf")
            db.save(file_hash, result)

    Args:
        pdf_path  (str | Path): Path to the PDF file.
        algorithm (str)       : Any algorithm name accepted by hashlib
                                (e.g. "sha256", "md5", "sha1"). Defaults to "sha256".

    Returns:
        str: Hex-encoded digest string (e.g. "a3f1d8...").
    """
    h = hashlib.new(algorithm)
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()