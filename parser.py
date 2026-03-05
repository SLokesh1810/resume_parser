import re
import os
import json
from pathlib import Path
import pdfplumber
import spacy
import pytesseract
from pdf2image import convert_from_path
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

BASE_DIR = Path.cwd()
RESOURCE_DIR = BASE_DIR / "Resource files"

class ResumeParser():
    def __init__(self, path, resource_dir, poppler_path=None):
        self.resource_dir = resource_dir
        self.poppler_path = poppler_path

        # Importing all JSON
        # JSON structure: 
        # {
        #     canonical: 'Name' <str>,
        #     aliases: ['similar names'] <list>
        # }
        self.SECTION_HEADERS = self.load_json("SectionHeaders.json")
        self.SKILLS_DB = self.load_json("Skills.json")
        self.EDUCATION_DB = self.load_json("Education.json")
        self.JOB_ROLES_DB = self.load_json("JobRoles.json")
        self.CERTS_DB = self.load_json("Certificates.json")
        self.data = self.parse_resume(path)

    def __str__(self):
        return json.dumps(self.data, indent=4)
        
    # REGEX patterns used
    EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    PHONE_REGEX = r'''
    (?:\+?\d{1,3}[\s\-]?)?
    (?:\(?\d{3}\)?[\s\-]?)?
    \d{3}[\s\-]?\d{4}
    '''
    LINK_REGEX = r'https?://[^\s/$.?#].[^\s]*'
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

    # To read json and store them as dictionaries
    def load_json(self, filename):
        with open(self.resource_dir / filename, "r", encoding="utf-8") as f:
            return json.load(f)

    # Cleans text, removes pointers (like, \uf0b7) and excess spacing
    def clean_text(self, text):
        text = text.replace("\xa0", " ")
        text = text.replace("\uf0b7", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def normalize_lines(self, text):
        return [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

    def normalize_text(self, text):
        if not text:
            return ""

        if not isinstance(text, str):
            text = str(text)

        text = re.sub(r"\. ", ".", text)
        text = re.sub(r"\|", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s*-\s*", "-", text)

        return text.lower().strip()

    # PDF decider, checks whether the pdf is text-based or image-based
    # How it works:
    # 1 - Try to extract assuming it's text-based
    # 2 - If contents are properly extracted (if failed_checks < 2), then proceeds with proper text-based extraction
    # 3 - Else (if failed_checks >= 2), uses OCR and POPPLER for extraction
    def pdf_extractor(self, pdf_path):
        text,_ = self.extract_text_from_pdf(pdf_path)
        cleaned = re.sub(r"\s+", " ", text).strip()

        personal_info = self.extract_personal_info(cleaned)
        sections = self.extract_sections(cleaned)
        skills = self.extract_skills(sections.get("skills", cleaned))
        education = self.extract_education(sections.get("education", ""))
        experience = self.extract_experience(sections.get("experience", ""))
        failed_checks = 0

        if not personal_info:
            failed_checks += 1
        if not sections:
            failed_checks += 1
        if not skills:
            failed_checks += 1
        if not education and not experience:
            failed_checks += 1

        if failed_checks >= 2:
            print("[INFO] Weak semantic extraction → OCR fallback")
            return self.extract_text_with_ocr(pdf_path)

        return text, 'text'

    # Extract PDF with OCR for image-based resume (eg, build with canva)
    def extract_text_with_ocr(self, pdf_path):
        text = ""
        if self.poppler_path:
            images = convert_from_path(pdf_path, poppler_path=self.poppler_path)
        else:
            images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"

        text = re.sub(r'[^\x00-\x7F]+', ' ', text)

        return text, 'ocr'

    # Extract text-based or ATS-friendly resumes
    def extract_text_from_pdf(self, pdf_path):
        lines = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(use_text_flow=True)

                line = []
                prev_top = None

                for w in words:
                    if prev_top is None or abs(w["top"] - prev_top) < 3:
                        line.append(w["text"])
                    else:
                        lines.append(" ".join(line))
                        line = [w["text"]]

                    prev_top = w["top"]

                if line:
                    lines.append(" ".join(line))

        return "\n".join(lines), 'text'

    # Divides sections on the resume
    # Text -> Dictionary (Section_name: Content)
    def extract_sections(self, text):
        positions = []
        text_lower = text.lower()

        # Step 1: find all section headers (aliases → canonical)
        for section in self.SECTION_HEADERS:
            canonical = section["canonical"]
            
            # loops over each alias of a specific canonical
            for alias in section["aliases"]:
                pattern = rf"\b{re.escape(alias)}\b\s*(?:[:\-]|\n)"
                for match in re.finditer(pattern, text_lower):
                    positions.append((match.start(), match.end(), canonical))

        # Step 2: sort by appearance
        positions.sort(key=lambda x: x[0])

        sections = {}

        # Step 3: slice safely using exact match boundaries
        for i, (start, header_end, canonical) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)

            section_text = text[header_end:end].strip()

            # Merge repeated sections (experience + internships etc.)
            if canonical in sections:
                sections[canonical] += "\n" + section_text
            else:
                sections[canonical] = section_text

        return sections

    # Divides sections for OCR-parsed resume
    def extract_sections_ocr(self, raw_text):
        positions = []
        lines = self.normalize_lines(raw_text)
        
        for idx, line in enumerate(lines):
            clean = line.lower().strip()

            for section in self.SECTION_HEADERS:
                heading = section["canonical"]
                keywords = section["aliases"]
                if clean in keywords or any(clean.startswith(k) for k in keywords):
                    positions.append((idx, heading))
                    break

        section_positions = positions
        sections = {}

        for i, (start_idx, section) in enumerate(section_positions):
            end_idx = (
                section_positions[i + 1][0]
                if i + 1 < len(section_positions)
                else len(lines)
            )

            content = lines[start_idx + 1 : end_idx]
            sections[section] = content

        structured_sections = {}
        for section, content_lines in sections.items():
            structured_sections[section] = "\n".join(content_lines).strip()
            structured_sections[section] = structured_sections[section].replace("\n"," ")
        
        return structured_sections
        
    def extract_personal_info(self, text):
        # Name parsing
        name = text[0] if text else None

        # Phone numbers parsing
        phones = re.findall(self.PHONE_REGEX, text, re.VERBOSE)
        phone_no = list(set(p.strip() for p in phones if p.strip()))

        # Mail parsing
        mail = list(set(re.findall(self.EMAIL_REGEX, text)))

        # Links parsing (includes only https links)
        links = list(set(re.findall(self.LINK_REGEX, text)))
        
        return {'name': name, 'phone': phone_no, 'mail': mail, 'links': links}

    def extract_skills(self, skills_text):
        text = self.normalize_text(skills_text)
        found_skills = set()

        for skill in self.SKILLS_DB:
            canonical = skill["skill"]
            for alias in skill["aliases"]:
                pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
                if re.search(pattern, text):
                    found_skills.add(canonical)
                    break

        return sorted(found_skills)

    def extract_certificates(self, cert_text):
        text = self.normalize_text(cert_text)
        found_certs = []

        for cert in self.CERTS_DB:
            canonical = cert["canonical"]
            issuer = cert.get("issuer")

            aliases = cert["aliases"] + [canonical.lower()]

            for alias in aliases:
                pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
                if re.search(pattern, text):
                    found_certs.append({
                        "name": canonical,
                        "issuer": issuer,
                        "type": "standard"
                    })
                    break  # stop after first alias match

        return found_certs

    def extract_non_standard_certificates(self, cert_text):
        text = self.normalize_text(cert_text)
        matches = []

        for m in re.finditer(self.NON_STANDARD_CERT_REGEX, text, re.I | re.VERBOSE):
            matches.append({
                "name": m.group().strip(),
                "issuer": m.group(1).title(),
                "type": "non-standard"
            })

        return matches

    def extract_all_certificates(self, cert_text):
        standard = self.extract_certificates(cert_text)
        non_standard = self.extract_non_standard_certificates(cert_text)

        return {
            "standard": standard,
            "non_standard": non_standard
        }

    def extract_education(self, education_text):
        if not education_text:
            return []

        text = self.normalize_text(education_text)
        
        # ---- STEP 1: Find degree alias positions (boundary detection) ----
        positions = []

        for entry in self.EDUCATION_DB:
            for alias in entry["aliases"]:
                pattern = rf"\b{re.escape(alias)}\b"
                for match in re.finditer(pattern, text):
                    positions.append((match.start(), entry))

        if not positions:
            return []

        # Sort by appearance in text
        positions.sort(key=lambda x: x[0])

        education_entries = []

        # ---- STEP 2: Split into blocks & parse each block ----
        for i, (start, entry) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            block = text[start:end].strip()

            edu = {
                "degree": entry["canonical"],
                "level": entry["level"].capitalize(),
                "specialization": None,
                "institution": None,
                "duration": None,
                "score": None
            }

            # ---- specialization ----
            for spec in entry.get("specializations", []):
                if spec in block:
                    edu["specialization"] = spec.capitalize()
                    break

            # ---- duration ----
            dur = re.search(self.DURATION_REGEX, block, re.IGNORECASE | re.VERBOSE)
            if dur:
                edu["duration"] = dur.group().strip()

            # ---- score ----
            score = re.search(
                r"\b\d{1,2}\.\d{1,2}\s*/\s*\d{1,2}|\b\d{1,3}\s*%",
                block
            )
            if score:
                edu["score"] = score.group().capitalize()

            # ---- institution ----
            inst = re.search(
                r"([A-Z][A-Za-z&.\s]{5,}?(University|Institute|College|Academy|School))",
                block
            )
            if inst:
                edu["institution"] = inst.group().strip().capitalize()

            education_entries.append(edu)

        return education_entries
        
    def extract_experience(self, exp_text):
        if not exp_text:
            return []

        text = self.normalize_text(exp_text)

        positions = []

        # -------- STEP 1: detect role vs duration anchor --------
        first_role_pos = None
        first_dur_pos = None

        for entry in self.JOB_ROLES_DB:
            for alias in entry["aliases"]:
                m = re.search(rf"\b{re.escape(alias)}\b", text)
                if m:
                    if first_role_pos is None or m.start() < first_role_pos:
                        first_role_pos = m.start()

        m = re.search(self.DURATION_REGEX, text, re.I | re.VERBOSE)
        if m:
            first_dur_pos = m.start()

        if first_role_pos is None and first_dur_pos is None:
            return []

        anchor_type = "duration" if (
            first_dur_pos is not None and
            (first_role_pos is None or first_dur_pos < first_role_pos)
        ) else "role"

        # -------- STEP 2: collect anchor positions --------
        if anchor_type == "role":
            aliases = []
            for entry in self.JOB_ROLES_DB:
                for alias in entry["aliases"]:
                    aliases.append((alias, entry))
            aliases.sort(key=lambda x: len(x[0]), reverse=True)

            for alias, entry in aliases:
                for m in re.finditer(rf"\b{re.escape(alias)}\b", text):
                    positions.append((m.start(), m.end(), alias, entry))
        else:
            for m in re.finditer(self.DURATION_REGEX, text, re.I | re.VERBOSE):
                positions.append((m.start(), m.end(), None, None))

        if not positions:
            return []

        positions.sort(key=lambda x: x[0])
        experiences = []

        # -------- STEP 3: split into blocks --------
        for i, (start, end_alias, alias, entry) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            block = text[start:end].strip()

            exp = {
                "role": entry["canonical"] if entry else None,
                "category": entry["category"] if entry else None,
                "company": None,
                "duration": None,
                "description": None
            }

            # ---- duration ----
            dur = re.search(self.DURATION_REGEX, block, re.I | re.VERBOSE)
            if dur:
                exp["duration"] = dur.group().strip()

            # ---- role (duration-first resumes) ----
            if exp["role"] is None:
                for r in self.JOB_ROLES_DB:
                    for a in r["aliases"]:
                        if re.search(rf"\b{re.escape(a)}\b", block):
                            exp["role"] = r["canonical"]
                            exp["category"] = r["category"]
                            alias = a
                            break

            m = re.search(self.COMPANY_REGEX, block, re.VERBOSE)
            if m:
                exp["company"] = m.group(1).strip()

            exp["description"] = block.strip()
            experiences.append(exp)

        return experiences

    def extract_projects(self, project_text):
        if not project_text:
            return []

        text = project_text.strip()

        projects = []

        # ---- STEP 1: Split project blocks ----
        split_pattern = r"(?:\d+\.\s+|•\s+|-+\s+)"
        blocks = re.split(split_pattern, text)

        
        for block in blocks:
            block = block.strip()
            if len(block) < 20:
                continue

            project = {
                "title": None,
                "tech_stack": [],
                "links": [],
                "description": None
            }

            # ---- STEP 3: Extract links (GitHub / Live URLs) ----
            links = re.findall(self.LINK_REGEX, block)
            if links:
                project["links"] = list(set(links))
                for l in links:
                    block = block.replace(l, "")

            # ---- STEP 4: Tech stack extraction ----
            tech_match = re.search(
                r"(tech\s*stack|tools|technologies|stack)\s*[:\-]\s*(.+)",
                block,
                re.IGNORECASE
            )

            if tech_match:
                tech_text = self.normalize_text(tech_match.group(2))
                for skill in self.SKILLS_DB:
                    for alias in skill["aliases"]:
                        if re.search(rf"\b{re.escape(alias)}\b", tech_text):
                            project["tech_stack"].append(skill["skill"])
                
                block = block.replace(tech_match.group(0), "")

            project["tech_stack"] = sorted(set(project["tech_stack"]))

            # ---- STEP 5: Project title ----
            title_parts = re.split(r"[–\-:]", block, maxsplit=1)
            title_raw = title_parts[0]
            
            title_candidate = re.sub(r"^\d+\.\s*", "", title_raw)
            project["title"] = title_raw.strip()
            
            if len(title_parts) > 1:
                block = title_parts[1]
            else:
                block = block.replace(title_raw, "", 1)

            # ---- STEP 6: Description ----
            project["description"] = block.strip()

            projects.append(project)

        return projects
                    
    def parse_resume(self, pdf_path):
        text, resume_type = self.pdf_extractor(pdf_path)
        
        if resume_type == 'text':
            text = self.clean_text(text)
            sections = self.extract_sections(text)
        else:
            sections = self.extract_sections_ocr(text)
        
        self.data = {
            "personal info": self.extract_personal_info(text),
            "education": self.extract_education(sections.get('education')),
            "skills": self.extract_skills(text),
            "experience": self.extract_experience(sections.get('experience')),
            "projects": self.extract_projects(sections.get('projects')),
            "certifications": self.extract_all_certificates(sections.get('certificates'))
        }
        return self.data

if __name__ == "__main__":
    parsed = ResumeParser(r"data/Resume - Lokesh (1).pdf", RESOURCE_DIR, poppler_path=POPPLER_PATH)
    print(parsed)