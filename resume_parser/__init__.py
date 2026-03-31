"""
resume_parser
=============
Public API for the resume parser module.

Usage:
    from resume_parser import parse_resume, hash_resume

    json_str = parse_resume("path/to/resume.pdf")
    file_hash = hash_resume("path/to/resume.pdf")
"""

from .parser import ResumeParser
from .config import RESOURCE_DIR, POPPLER_PATH
from .utils  import hash_resume


def parse_resume(path, resource_dir=None, poppler_path=None) -> str:
    """
    Parse a resume PDF and return the structured data as a JSON string.

    Args:
        path         (str | Path): Path to the resume PDF.
        resource_dir (str | Path): Directory containing JSON resource files.
                                   Defaults to the built-in Resource files/ directory.
        poppler_path (str | Path): Poppler binary path (Windows only; None on Linux/macOS).

    Returns:
        str: JSON string with keys:
             personal_info, education, skills, experience, projects, certifications.
    """
    rdir  = resource_dir or RESOURCE_DIR
    ppath = poppler_path or POPPLER_PATH
    parser = ResumeParser(path, resource_dir=rdir, poppler_path=ppath)
    return parser.to_json()


__all__ = ["parse_resume", "hash_resume", "ResumeParser"]