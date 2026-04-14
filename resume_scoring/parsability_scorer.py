import re

def character_scorer(raw_text, parsed_data):
    if not raw_text:
        return 0

    total_chars = len(raw_text)

    # -------------------------
    # 1. Extract parsed text
    # -------------------------
    parsed_text = ""

    for e in parsed_data.get("experience", []):
        parsed_text += e.get("description", "") + " "

    for p in parsed_data.get("projects", []):
        parsed_text += p.get("description", "") + " "

    for skill in parsed_data.get("skills", []):
        parsed_text += skill + " "

    # -------------------------
    # 2. Coverage score (char-level)
    # -------------------------
    raw_set = set(raw_text.lower())
    parsed_set = set(parsed_text.lower())

    coverage = len(parsed_set & raw_set) / max(len(raw_set), 1)

    coverage_score = coverage * 70  # main weight

    # -------------------------
    # 3. Noise penalty
    # -------------------------
    weird_chars = re.findall(r"[^\x00-\x7F]", raw_text)
    noise_ratio = len(weird_chars) / total_chars

    noise_penalty = min(noise_ratio * 100, 20)

    # -------------------------
    # 4. Bullet / symbol detection
    # -------------------------
    bullets = re.findall(r"[•▪●■]", raw_text)
    bullet_penalty = min(len(bullets) * 0.5, 10)

    # -------------------------
    # FINAL
    # -------------------------
    score = coverage_score - noise_penalty - bullet_penalty

    return max(0, min(score, 100))

def design_penalty_scorer(design_meta, resume_type):
    penalty = 0

    if design_meta["image_count"] > 2:
        penalty += 10

    if design_meta["pages_with_images"] > 0:
        penalty += 5

    if design_meta["low_text_pages"] > 0:
        penalty += 10

    if resume_type == "ocr":
        penalty += 10

    return min(penalty, 30)