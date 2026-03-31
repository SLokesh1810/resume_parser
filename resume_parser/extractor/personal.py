"""
extractor/personal.py
=====================
Extracts personal / contact information from resume text.

Fields extracted:
  - name   : assumed to be the very first token on the first line.
  - phone  : all phone numbers found, de-duplicated.
  - mail   : all e-mail addresses found, de-duplicated.
  - links  : all https:// URLs found, de-duplicated.
"""

import re

# ── Compiled patterns ────────────────────────────────────────────────────────

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

PHONE_REGEX = r"""
(?:\+?\d{1,3}[\s\-]?)?
(?:\(?\d{3}\)?[\s\-]?)?
\d{3}[\s\-]?\d{4}
"""

LINK_REGEX = r"https?://[^\s/$.?#].[^\s]*"


def extract_personal_info(text: str) -> dict:
    """
    Parse personal contact details from *text*.

    Args:
        text (str): Full resume text (clean or OCR-extracted).

    Returns:
        dict with keys: name, phone, mail, links.
    """
    # Name: first non-empty character sequence on the very first line
    first_line = text.split("\n")[0].strip() if text else ""
    name = first_line if first_line else None

    # Phone numbers
    phones = re.findall(PHONE_REGEX, text, re.VERBOSE)
    phone_no = list(set(p.strip() for p in phones if p.strip()))

    # E-mail addresses
    mail = list(set(re.findall(EMAIL_REGEX, text)))

    # Hyperlinks
    links = list(set(re.findall(LINK_REGEX, text)))

    return {
        "name":  name,
        "phone": phone_no,
        "mail":  mail,
        "links": links,
    }