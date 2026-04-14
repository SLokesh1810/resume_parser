"""
extractor/projects.py
=====================
Parses the projects section into structured records.

Each record contains:
  - title       : project name
  - tech_stack  : list of canonical skill names detected in the stack
  - links       : list of URLs (GitHub, live demos, etc.)
  - description : remaining text after removing title / links / tech stack
"""

import re
from resume_parser.utils import normalize_text

LINK_REGEX = r"https?://[^\s/$.?#].[^\s]*"


def extract_projects(project_text: str, skills_db: list[dict]) -> list[dict]:
    """
    Extract project entries from *project_text*.

    Args:
        project_text (str)       : Text from the projects section.
        skills_db    (list[dict]): Skills knowledge-base for tech-stack matching.

    Returns:
        list[dict]: Each dict has keys: title, tech_stack, links, description.
    """
    if not project_text:
        return []

    text = project_text.strip()
    projects: list[dict] = []

    # Split into individual project blocks on common list markers
    split_pattern = r"(?:\d+\.\s+|•\s+|-+\s+)"
    blocks = re.split(split_pattern, text)

    for block in blocks:
        block = block.strip()
        if len(block) < 20:
            continue

        project: dict = {
            "title":       None,
            "tech_stack":  [],
            "links":       [],
            "description": None,
        }

        # ── Links ────────────────────────────────────────────────────────────
        links = re.findall(LINK_REGEX, block)
        if links:
            project["links"] = list(set(links))
            for link in links:
                block = block.replace(link, "")

        # ── Tech stack ───────────────────────────────────────────────────────
        tech_match = re.search(
            r"(tech\s*stack|tools|technologies|stack)\s*[:\-]\s*(.+)",
            block,
            re.IGNORECASE,
        )
        if tech_match:
            tech_text = normalize_text(tech_match.group(2))
            for skill in skills_db:
                for alias in skill["aliases"]:
                    if re.search(rf"\b{re.escape(alias)}\b", tech_text):
                        project["tech_stack"].append(skill["skill"])
                        break
            block = block.replace(tech_match.group(0), "")

        project["tech_stack"] = sorted(set(project["tech_stack"]))

        # ── Title ────────────────────────────────────────────────────────────
        title_parts = re.split(r"[–\-:]", block, maxsplit=1)
        title_raw = title_parts[0]
        project["title"] = re.sub(r"^\d+\.\s*", "", title_raw).strip()

        # ── Description ──────────────────────────────────────────────────────
        project["description"] = block.strip()

        projects.append(project)

    return projects