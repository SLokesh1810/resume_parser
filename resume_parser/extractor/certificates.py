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


def extract_certificates(cert_text: str, certs_db: list[dict]) -> list[dict]:
    """
    Match text against the standard certifications knowledge-base.

    Args:
        cert_text (str)       : Text from the certifications section.
        certs_db  (list[dict]): Knowledge-base; each entry has "canonical",
                                "aliases", and optionally "issuer".

    Returns:
        list[dict]: Each dict has keys: name, issuer, type="standard".
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


def extract_non_standard_certificates(cert_text: str) -> list[dict]:
    """
    Use a regex to detect online-platform / MOOC certificates.

    Args:
        cert_text (str): Text from the certifications section.

    Returns:
        list[dict]: Each dict has keys: name, issuer, type="non-standard".
    """
    if not cert_text:
        return []

    text = normalize_text(cert_text)
    matches: list[dict] = []

    for m in re.finditer(NON_STANDARD_CERT_REGEX, text, re.I | re.VERBOSE):
        matches.append({
            "name":   m.group().strip(),
            "issuer": m.group(1).title(),
            "type":   "non-standard",
        })

    return matches


def extract_all_certificates(cert_text: str, certs_db: list[dict]) -> dict:
    """
    Combine standard and non-standard certificate extraction.

    Returns:
        dict with keys "standard" and "non_standard", each a list of dicts.
    """
    return {
        "standard":     extract_certificates(cert_text, certs_db),
        "non_standard": extract_non_standard_certificates(cert_text),
    }