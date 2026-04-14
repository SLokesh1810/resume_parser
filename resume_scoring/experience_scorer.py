import re
import spacy
from resume_scoring.word_lists import (
    IMPACT_WORDS,
    ACTION_VERBS,
    RESPONSIBILITY_WORDS,
    WEAK_WORDS,
    METRIC_WORDS
)

# Load NLP model once
nlp = spacy.load("en_core_web_sm")


# =========================
# PREPROCESSING
# =========================
def preprocess(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc]


# =========================
# IMPACT SCORE
# =========================
def impact_score(lemmas):
    count = sum(1 for w in IMPACT_WORDS if w in lemmas)
    return min(count * 8, 25)


# =========================
# QUANT SCORE
# =========================
def quant_score(text):
    nums = re.findall(r'\b\d+(\.\d+)?\+?%?\b', text)

    score = len(nums) * 5

    # Bonus for strong metrics
    if any(m in text.lower() for m in METRIC_WORDS):
        score += 5

    if "%" in text:
        score += 10

    return min(score, 20)


# =========================
# ACTION SCORE
# =========================
def action_score(lemmas):
    count = sum(1 for w in ACTION_VERBS if w in lemmas)
    return min(count * 5, 15)


# =========================
# TECH SCORE
# =========================
def tech_score(text, skills_list):
    text = text.lower()
    count = sum(1 for skill in skills_list if skill.lower() in text)
    return min(count * 4, 20)


# =========================
# RESPONSIBILITY SCORE
# =========================
def responsibility_score(lemmas):
    count = sum(1 for w in RESPONSIBILITY_WORDS if w in lemmas)
    return min(count * 5, 10)


# =========================
# WEAK PENALTY
# =========================
def penalty_score(text):
    text = text.lower()
    return -10 if any(w in text for w in WEAK_WORDS) else 0


# =========================
# DURATION SCORE
# =========================
def duration_score(duration_text):
    if not duration_text:
        return 0

    duration_text = duration_text.lower()

    if "year" in duration_text:
        return 10
    if "month" in duration_text or "-" in duration_text:
        return 6

    return 4

# =========================
# FINAL EXPERIENCE SCORE
# =========================
def experience_scorer(exp, skills_list):
    text = exp["description"]
    lemmas = preprocess(text)
    category = exp.get("category", "").lower()

    if "intern" in category:
        # Less strict on responsibility & impact
        score = (
            impact_score(lemmas) * 0.7 +
            quant_score(text) +
            action_score(lemmas) +
            tech_score(text, skills_list) * 1.2 +
            responsibility_score(lemmas) * 0.5 +
            duration_score(exp.get("duration", "")) +
            penalty_score(text)
        )
    else:
        # Full strict scoring
        score = (
            impact_score(lemmas) +
            quant_score(text) +
            action_score(lemmas) +
            tech_score(text, skills_list) +
            responsibility_score(lemmas) +
            duration_score(exp.get("duration", "")) +
            penalty_score(text)
        )

    return max(0, min(score, 100))