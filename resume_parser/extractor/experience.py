"""
extractor/experience.py
=======================
Parses the experience / work-history section into structured records.

Strategy:
  1. Determine whether the resume anchors entries on job *roles* or *durations*
     (whichever appears first in the text wins).
  2. Collect all anchor positions and slice the text into per-entry blocks.
  3. Extract role, company, duration, and a raw description from each block.
"""

import re
from resume_parser.utils import normalize_text

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

COMPANY_REGEX = r"""
(?:-|@|\|)?\s*
([A-Z][A-Za-z0-9&., ]{2,})
(?=\s*(?:\(|\||-|,|\d{4}|present|current|$))
"""


def extract_experience(exp_text: str, job_roles_db: list[dict], skills_db: list[dict]) -> list[dict]:
    """
    Extract work-experience entries from *exp_text*.

    Args:
        exp_text     (str)       : Text from the experience section.
        job_roles_db (list[dict]): Knowledge-base; each entry has "canonical",
                                   "category", and "aliases".

    Returns:
        list[dict]: Ordered list of experience records, each with keys:
                    role, category, company, duration, description.
    """
    if not exp_text:
        return []

    text = normalize_text(exp_text)

    # ── Step 1: decide anchor type ────────────────────────────────────────────
    first_role_pos: int | None = None
    first_dur_pos:  int | None = None

    for entry in job_roles_db:
        for alias in entry["aliases"]:
            m = re.search(rf"\b{re.escape(alias)}\b", text)
            if m:
                if first_role_pos is None or m.start() < first_role_pos:
                    first_role_pos = m.start()

    m = re.search(DURATION_REGEX, text, re.I | re.VERBOSE)
    if m:
        first_dur_pos = m.start()

    if first_role_pos is None and first_dur_pos is None:
        return []

    anchor_type = "duration" if (
        first_dur_pos is not None and
        (first_role_pos is None or first_dur_pos < first_role_pos)
    ) else "role"

    # ── Step 2: collect anchor positions ─────────────────────────────────────
    positions: list[tuple] = []

    if anchor_type == "role":
        # Sort aliases longest-first to prefer specific matches
        aliases = []
        for entry in job_roles_db:
            for alias in entry["aliases"]:
                aliases.append((alias, entry))
        aliases.sort(key=lambda x: len(x[0]), reverse=True)

        for alias, entry in aliases:
            for m in re.finditer(rf"\b{re.escape(alias)}\b", text):
                positions.append((m.start(), m.end(), alias, entry))
    else:
        for m in re.finditer(DURATION_REGEX, text, re.I | re.VERBOSE):
            positions.append((m.start(), m.end(), None, None))

    if not positions:
        return []

    positions.sort(key=lambda x: x[0])
    experiences: list[dict] = []

    # ── Step 3: slice into blocks and extract fields ──────────────────────────
    for i, (start, end_alias, alias, entry) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        block = text[start:end].strip()

        exp: dict = {
            "role":        entry["canonical"] if entry else None,
            "category":    entry["category"]  if entry else None,
            "company":     None,
            "duration":    None,
            "skills":      [],
            "description": None,
        }

        # Duration
        dur = re.search(DURATION_REGEX, block, re.I | re.VERBOSE)
        if dur:
            exp["duration"] = dur.group().strip()

        # Role (for duration-first resumes)
        if exp["role"] is None:
            for r in job_roles_db:
                for a in r["aliases"]:
                    if re.search(rf"\b{re.escape(a)}\b", block):
                        exp["role"]     = r["canonical"]
                        exp["category"] = r["category"]
                        break

        # Company
        cm = re.search(COMPANY_REGEX, block, re.VERBOSE)
        if cm:
            exp["company"] = cm.group(1).strip()

        for skill in skills_db:
            for alias in skill["aliases"]:
                if re.search(rf"\b{re.escape(alias)}\b", block):
                    exp["skills"].append(skill["skill"])
                    break

        exp["description"] = block.strip()
        experiences.append(exp)

    return experiences