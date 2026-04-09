"""
parser.py
=========
ResumeParser — the central orchestrator that ties every sub-module together.

Typical usage (via the module's public API):

    from resume_parser import parse_resume
    data = parse_resume("my_resume.pdf")

Or directly:

    from resume_parser.parser import ResumeParser
    parser = ResumeParser("my_resume.pdf", resource_dir=..., poppler_path=...)
    print(parser)          # pretty-printed JSON
    data = parser.data     # plain Python dict
"""

import json
from pathlib import Path

from resume_parser.config import RESOURCE_DIR, POPPLER_PATH
from resume_parser.loader import load_all
from resume_parser.utils import clean_text

from resume_parser.extractor.pdf          import extract_pdf
from resume_parser.extractor.sections     import extract_sections, extract_sections_ocr
from resume_parser.extractor.skills       import extract_skills
from resume_parser.extractor.education    import extract_education
from resume_parser.extractor.experience   import extract_experience
from resume_parser.extractor.projects     import extract_projects
from resume_parser.extractor.certificates import extract_all_certificates


class ResumeParser:
    """
    Parse a PDF resume and expose the result as a Python dict and as JSON.

    Args:
        path         (str | Path): Path to the PDF resume.
        resource_dir (Path)      : Directory containing JSON knowledge-base files.
        poppler_path (str | None): Poppler binary path (Windows only; None on
                                   Linux / macOS where it is on the system PATH).
    """

    def __init__(self, path, resource_dir: Path = RESOURCE_DIR, poppler_path=POPPLER_PATH):
        self.resource_dir = Path(resource_dir)
        self.poppler_path = poppler_path

        # Load all knowledge-base JSON files once
        db = load_all(self.resource_dir)
        self._section_headers = db["section_headers"]
        self._skills_db       = db["skills"]
        self._education_db    = db["education"]
        self._job_roles_db    = db["job_roles"]
        self._certs_db        = db["certificates"]

        # Run the full parsing pipeline
        self.data = self._parse_resume(path)

    # ── Public interface ──────────────────────────────────────────────────────

    def __str__(self) -> str:
        """Return the parsed data as an indented JSON string."""
        return json.dumps(self.data, indent=4)

    def to_json(self, indent: int = 4) -> str:
        """Serialise the parsed data to a JSON string."""
        return json.dumps(self.data, indent=indent)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _section_extractor(self, text: str) -> dict:
        return extract_sections(text, self._section_headers)

    def _section_extractor_ocr(self, text: str) -> dict:
        return extract_sections_ocr(text, self._section_headers)

    def _parse_resume(self, pdf_path) -> dict:
        """
        Full parsing pipeline:
          1. Extract raw text (text-based or OCR).
          2. Split into sections.
          3. Run each field extractor on the relevant section.
        """
        # Pass lightweight extractor callables so extract_pdf can do its
        # quality-check without importing this module (avoids circular imports).
        quality_extractors = {
            "sections":      self._section_extractor,
            "skills":        lambda t: extract_skills(t, self._skills_db),
            "education":     lambda t: extract_education(t, self._education_db),
            "experience":    lambda t: extract_experience(t, self._job_roles_db),
        }

        text, resume_type = extract_pdf(
            pdf_path,
            poppler_path=self.poppler_path,
            extractors=quality_extractors,
        )

        if resume_type == "text":
            text     = clean_text(text)
            sections = extract_sections(text, self._section_headers)
        else:
            sections = extract_sections_ocr(text, self._section_headers)

        return {
            "education":      extract_education(sections.get("education", ""),    self._education_db),
            "skills":         extract_skills(sections.get("skills", text),        self._skills_db),
            "experience":     extract_experience(sections.get("experience", ""),  self._job_roles_db),
            "projects":       extract_projects(sections.get("projects", ""),      self._skills_db),
            "certifications": extract_all_certificates(sections.get("certificates", ""), self._certs_db),
        }