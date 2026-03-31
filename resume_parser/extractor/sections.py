"""
extractor/sections.py
=====================
Splits raw resume text into named sections (e.g. "experience", "education").

Two strategies mirror the two PDF-extraction modes:
  - extract_sections      : regex-based, for clean digital text.
  - extract_sections_ocr  : line-by-line, for noisier OCR output.
"""

import re
from resume_parser.utils import normalize_lines


def extract_sections(text: str, section_headers: list[dict]) -> dict[str, str]:
    """
    Identify section headers in *text* and return a dict mapping each
    canonical section name to its content.

    Sections defined in *section_headers* are matched by their aliases.
    Duplicate canonical sections (e.g. "experience" appearing twice) are
    concatenated.

    Args:
        text            (str)       : Raw resume text.
        section_headers (list[dict]): Knowledge-base list, each entry has
                                      "canonical" and "aliases" keys.

    Returns:
        dict[str, str]: { canonical_section_name: section_text, ... }
    """
    positions: list[tuple[int, int, str]] = []
    text_lower = text.lower()

    for section in section_headers:
        canonical = section["canonical"]
        for alias in section["aliases"]:
            pattern = rf"\b{re.escape(alias)}\b\s*(?:[:\-]|\n)"
            for match in re.finditer(pattern, text_lower):
                positions.append((match.start(), match.end(), canonical))

    positions.sort(key=lambda x: x[0])

    sections: dict[str, str] = {}
    for i, (start, header_end, canonical) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        section_text = text[header_end:end].strip()

        if canonical in sections:
            sections[canonical] += "\n" + section_text
        else:
            sections[canonical] = section_text

    return sections


def extract_sections_ocr(raw_text: str, section_headers: list[dict]) -> dict[str, str]:
    """
    Line-by-line section splitter designed for OCR output where whitespace
    and punctuation may be inconsistent.

    Args:
        raw_text        (str)       : OCR-extracted resume text.
        section_headers (list[dict]): Knowledge-base list (same format as above).

    Returns:
        dict[str, str]: { canonical_section_name: section_text, ... }
    """
    lines = normalize_lines(raw_text)
    positions: list[tuple[int, str]] = []

    for idx, line in enumerate(lines):
        clean = line.lower().strip()
        for section in section_headers:
            canonical = section["canonical"]
            keywords = section["aliases"]
            if clean in keywords or any(clean.startswith(k) for k in keywords):
                positions.append((idx, canonical))
                break

    sections: dict[str, list[str]] = {}
    for i, (start_idx, canonical) in enumerate(positions):
        end_idx = positions[i + 1][0] if i + 1 < len(positions) else len(lines)
        content = lines[start_idx + 1: end_idx]
        sections[canonical] = content

    structured: dict[str, str] = {}
    for section, content_lines in sections.items():
        joined = "\n".join(content_lines).strip().replace("\n", " ")
        structured[section] = joined

    return structured