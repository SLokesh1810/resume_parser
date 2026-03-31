"""
extractor/skills.py
===================
Matches technical and soft skills against the Skills knowledge-base.

Uses whole-word regex matching so "R" does not match inside "React" etc.
"""

import re
from resume_parser.utils import normalize_text


def extract_skills(skills_text: str, skills_db: list[dict]) -> list[str]:
    """
    Find all skills present in *skills_text* and return their canonical names.

    Args:
        skills_text (str)       : Text from the skills section (or full resume).
        skills_db   (list[dict]): Knowledge-base; each entry has "skill" and
                                  "aliases" keys.

    Returns:
        list[str]: Sorted list of canonical skill names.
    """
    text = normalize_text(skills_text)
    found: set[str] = set()

    for skill in skills_db:
        canonical = skill["skill"]
        for alias in skill["aliases"]:
            pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
            if re.search(pattern, text):
                found.add(canonical)
                break  # no need to check remaining aliases

    return sorted(found)