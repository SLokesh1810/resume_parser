"""
extractor/education.py
======================
Parses the education section of a resume into structured records.

Each record contains:
  - degree         : canonical degree name (e.g. "Bachelor of Technology")
  - level          : study level (e.g. "undergraduate")
  - specialization : field of study if detected
  - institution    : college / university name
  - duration       : date range (e.g. "2020 - 2024")
  - score          : GPA or percentage if present
"""

import re
from resume_parser.utils import normalize_text

# Shared duration pattern (also used by experience.py)
DURATION_REGEX = r"""
(
    (?:\b\w+\b[\s,/.-]*)?
    (?:\d{1,2}[\s/.-]*)?
    \d{4}
)
\s*(?:–|-|to|until|till)\s*
(
    (?:\b\w+\b[\s,/.-]*)?
    (?:\d{1,2}[\s/.-]*)?
    (?:\d{4}|present|current|now)
)
"""


def extract_education(education_text: str, education_db: list[dict]) -> list[dict]:
    """
    Extract one structured dict per education entry found in *education_text*.

    Args:
        education_text (str)       : Text from the education section.
        education_db   (list[dict]): Knowledge-base; each entry has "canonical",
                                     "aliases", "level", and optionally
                                     "specializations".

    Returns:
        list[dict]: Ordered list of education records.
    """
    if not education_text:
        return []

    text = normalize_text(education_text)
    positions: list[tuple[int, dict]] = []

    # ── Step 1: locate degree aliases ────────────────────────────────────────
    for entry in education_db:
        for alias in entry["aliases"]:
            pattern = rf"\b{re.escape(alias)}\b"
            for match in re.finditer(pattern, text):
                positions.append((match.start(), entry))

    if not positions:
        return []

    positions.sort(key=lambda x: x[0])
    education_entries: list[dict] = []

    # ── Step 2: slice into blocks and parse each one ─────────────────────────
    for i, (start, entry) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        block = text[start:end].strip()

        edu: dict = {
            "degree":         entry["canonical"],
            "level":          entry["level"].capitalize(),
            "specialization": None,
            "institution":    None,
            "duration":       None,
            "score":          None,
        }

        # Specialization
        for spec in entry.get("specializations", []):
            if spec in block:
                edu["specialization"] = spec.capitalize()
                break

        # Duration
        dur = re.search(DURATION_REGEX, block, re.IGNORECASE | re.VERBOSE)
        if dur:
            edu["duration"] = dur.group().strip()

        # Score (GPA or percentage)
        score = re.search(
            r"\b\d{1,2}\.\d{1,2}\s*/\s*\d{1,2}|\b\d{1,3}\s*%",
            block
        )
        if score:
            edu["score"] = score.group().capitalize()

        # Institution
        inst = re.search(
            r"([A-Z][A-Za-z&.\s]{5,}?(University|Institute|College|Academy|School))",
            block
        )
        if inst:
            edu["institution"] = inst.group().strip().capitalize()

        education_entries.append(edu)

    return education_entries