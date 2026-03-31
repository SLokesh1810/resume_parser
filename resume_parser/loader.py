"""
loader.py
=========
Loads and caches the JSON knowledge-base files that drive extraction.

Each JSON file is expected to contain a list of objects with at least:
  - "canonical"  : the normalised output name
  - "aliases"    : list of alternative spellings / abbreviations
"""

import json
from pathlib import Path


def load_json(resource_dir: Path, filename: str) -> list[dict]:
    """
    Read a JSON file from *resource_dir* and return its contents.

    Args:
        resource_dir (Path): Directory that holds the JSON knowledge-base files.
        filename     (str) : JSON filename, e.g. "Skills.json".

    Returns:
        list[dict]: Parsed JSON content.

    Raises:
        FileNotFoundError: if the file does not exist in *resource_dir*.
    """
    filepath = resource_dir / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all(resource_dir: Path) -> dict[str, list]:
    """
    Load every knowledge-base file at once and return a named dictionary.

    Returns:
        dict with keys: section_headers, skills, education, job_roles, certificates
    """
    return {
        "section_headers": load_json(resource_dir, "SectionHeaders.json"),
        "skills":          load_json(resource_dir, "Skills.json"),
        "education":       load_json(resource_dir, "Education.json"),
        "job_roles":       load_json(resource_dir, "JobRoles.json"),
        "certificates":    load_json(resource_dir, "Certificates.json"),
    }