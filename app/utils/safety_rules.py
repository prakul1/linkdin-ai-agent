"""Safety rules for LinkedIn posts (rule-based = free)."""
import re
from typing import List, Tuple
BANNED_WORDS = {
    "stupid", "idiot", "dumb", "moron",
    "retard", "lame",
    "guaranteed millionaire", "get rich quick", "100% guaranteed",
    "click here now", "limited time only",
}
RISKY_PATTERNS = [
    (r"\$\d+[kKmM]?\s*(per|/)?\s*(day|week|month)", "Unrealistic income claims"),
    (r"\b(everyone|nobody|always|never)\s+(thinks|knows|does)", "Overgeneralization"),
    (r"\b(crypto|nft)\b.*\b(guaranteed|profit|returns)\b", "Crypto promotion red flag"),
]
MIN_LENGTH = 50
MAX_LENGTH = 3000
MAX_HASHTAGS = 8
def check_banned_words(text):
    text_lower = text.lower()
    return [w for w in BANNED_WORDS if w in text_lower]
def check_risky_patterns(text):
    matches = []
    for pattern, reason in RISKY_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            matches.append((m.group(0), reason))
    return matches
def check_length(text):
    issues = []
    if len(text) < MIN_LENGTH:
        issues.append(f"Too short ({len(text)} chars, min {MIN_LENGTH})")
    if len(text) > MAX_LENGTH:
        issues.append(f"Too long ({len(text)} chars, max {MAX_LENGTH})")
    return issues
def check_hashtag_count(text):
    hashtags = re.findall(r"#\w+", text)
    if len(hashtags) > MAX_HASHTAGS:
        return [f"Too many hashtags ({len(hashtags)}, max {MAX_HASHTAGS})"]
    return []
def run_all_safety_checks(text):
    issues = []
    banned = check_banned_words(text)
    if banned:
        issues.extend([f"Banned word: '{w}'" for w in banned])
    risky = check_risky_patterns(text)
    if risky:
        issues.extend([f"Risky: '{m}' ({r})" for m, r in risky])
    issues.extend(check_length(text))
    issues.extend(check_hashtag_count(text))
    score = 100
    score -= len(banned) * 40
    score -= len(risky) * 15
    score -= len(check_length(text)) * 10
    score -= len(check_hashtag_count(text)) * 5
    score = max(0, score)
    passed = score >= 60 and len(banned) == 0
    return {"passed": passed, "score": score, "issues": issues}