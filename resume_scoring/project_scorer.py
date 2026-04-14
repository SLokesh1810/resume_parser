import re
import spacy
from resume_scoring.word_lists import (
    IMPACT_WORDS,
    COMPARISON_WORDS,
    METRIC_WORDS,
    WEAK_WORDS,
    PIPELINE_WORDS,
    STRONG_PHRASES
)

# Load NLP model
nlp = spacy.load("en_core_web_sm")


# =========================
# PREPROCESSING
# =========================
def preprocess(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc]


# =========================
# QUANT SCORE
# =========================
def quant_score(text):
    nums = re.findall(r'\b\d+(\.\d+)?\+?%?\b', text)

    score = len(nums) * 10

    if "%" in text:
        score += 10

    if any(m in text.lower() for m in METRIC_WORDS):
        score += 5

    return min(score, 25)


# =========================
# IMPACT SCORE
# =========================
def impact_score(lemmas):
    count = sum(1 for w in IMPACT_WORDS if w in lemmas)
    return min(count * 10, 20)


# =========================
# COMPARISON SCORE
# =========================
def comparison_score(text):
    text = text.lower()
    count = sum(1 for w in COMPARISON_WORDS if w in text)
    return min(count * 15, 15)


# =========================
# TECH SCORE
# =========================
def tech_score(text, skills_list):
    text = text.lower()
    count = sum(1 for skill in skills_list if skill.lower() in text)
    return min(count * 5, 25)


# =========================
# PIPELINE DEPTH BONUS
# =========================
def pipeline_score(text):
    text = text.lower()
    count = sum(1 for w in PIPELINE_WORDS if w in text)
    return min(count * 3, 10)


# =========================
# STRONG PHRASE BONUS
# =========================
def strong_phrase_score(text):
    text = text.lower()
    return 5 if any(p in text for p in STRONG_PHRASES) else 0


# =========================
# WEAK PENALTY
# =========================
def penalty_score(text):
    text = text.lower()
    return -10 if any(w in text for w in WEAK_WORDS) else 0


# =========================
# CLARITY SCORE
# =========================
def clarity_score(text):
    sentences = text.split(".")
    return 15 if len(sentences) >= 2 else 5


# =========================
# FINAL PROJECT SCORE
# =========================
def project_scorer(text, skills_list):
    lemmas = preprocess(text)

    score = (
        quant_score(text) +
        impact_score(lemmas) +
        comparison_score(text) +
        tech_score(text, skills_list) +
        pipeline_score(text) +
        strong_phrase_score(text) +
        clarity_score(text) +
        penalty_score(text)
    )

    return max(0, min(score, 100))