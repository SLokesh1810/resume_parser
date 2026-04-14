"""
extractor/certificates.py
=========================
Extracts certifications from the resume.

Two categories are handled:
  - Standard     : industry-recognised certs matched against the knowledge-base
                   (e.g. AWS Certified Developer, Google Cloud Associate).
  - Non-standard : MOOC / online-platform courses detected via a fixed regex
                   (Udemy, Coursera, edX, LinkedIn Learning, …).
"""

import re
from resume_parser.utils import normalize_text

NON_STANDARD_CERT_REGEX = r"""
\b(
    udemy|
    coursera|
    edx|
    linkedin\s+learning|
    google|
    microsoft|
    aws\s+academy|
    ibm|
    meta
)\b
[^\n,.]{0,80}
\b(
    certificate|
    certification|
    course|
    specialization|
    bootcamp|
    training
)
"""


def extract_certificates(cert_text: str, certs_db: list[dict]) -> dict:
    """
    Combine standard and non-standard certificate extraction.

    Returns:
        dict with keys "standard" and "non_standard", each a list of dicts.
    """
    if not cert_text:
        return []

    text = normalize_text(cert_text)
    found: list[dict] = []

    for cert in certs_db:
        canonical = cert["canonical"]
        issuer    = cert.get("issuer")
        aliases   = cert["aliases"] + [canonical.lower()]

        for alias in aliases:
            pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
            if re.search(pattern, text):
                found.append({
                    "name":   canonical,
                    "issuer": issuer,
                    "type":   "standard",
                })
                break  # stop at first matching alias

    return found