import re
import math
from typing import Optional

ROBOTIC_CLICHES = [
    "delve into",
    "delving into",
    "delve deeper into",
    "can you delve into",
    "delve",
    "testament to",
    "stands as a testament",
    "rich tapestry",
    "tapestry",
    "in summary",
    "in conclusion",
    "to summarize",
    "pivotal role",
    "pivotal",
    "beacon of",
    "beacon",
    "furthermore",
    "moreover",
    "it is worth noting",
    "it is noteworthy",
    "it should be noted",
    "embark on",
    "embark upon",
    "embarking on",
    "foster",
    "fostering",
    "streamline",
    "streamlining",
    "leverage",
    "leveraging",
    "vital role",
    "crucial role",
    "plays a vital role",
    "game-changer",
    "game changer",
    "plethora",
    "myriad of",
    "myriad",
    "multifaceted",
    "multi-faceted",
    "underpins",
    "underpinning",
    "intertwined",
    "unwavering",
    "unwavering dedication",
    "deep dive",
    "harness the power of",
    "harnessing the power",
    "meticulous attention",
    "meticulous",
    "commendable",
    "notably",
    "at the forefront of",
    "bustling",
    "nestled",
    "without further ado",
    "it is important to remember",
]

# Compile regex patterns for word-boundary matching
_COMPILED_PATTERNS = [
    (phrase, re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE))
    for phrase in ROBOTIC_CLICHES
]

def detect_robotic_phrases(text: str) -> list[str]:
    """Detect presence of robotic AI clichés in the given text."""
    if not text or not text.strip():
        return []
    found = []
    seen = set()
    for phrase, pattern in _COMPILED_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            canonical = phrase.lower()
            if canonical not in seen:
                # Store the exact casing from text if possible, else the canonical
                found.append(matches[0])
                seen.add(canonical)
    return found

def _sentence_length_std_dev(text: str) -> tuple[int, float]:
    """Calculate sentence count and standard deviation of sentence lengths (in words)."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 0, 0.0
    lengths = [len(s.split()) for s in sentences]
    n = len(lengths)
    if n <= 1:
        return n, 10.0
    mean = sum(lengths) / n
    variance = sum((x - mean) ** 2 for x in lengths) / n
    return n, math.sqrt(variance)

def analyze_robotic_language(text: str, rewritten_text: Optional[str] = None) -> dict:
    """Analyze robotic language patterns, score, and compute eliminated phrases if rewritten_text provided."""
    cliches = detect_robotic_phrases(text)
    num_sentences, std_dev = _sentence_length_std_dev(text)
    
    cliche_count = len(cliches)
    if cliche_count >= 3 or (cliche_count >= 1 and num_sentences >= 2 and std_dev < 4.0):
        score = "High"
        description = "High density of typical AI clichés and uniform sentence structure detected."
    elif cliche_count >= 1 or (num_sentences >= 3 and std_dev < 4.5):
        score = "Medium"
        description = "Moderate robotic phrasing and predictable rhythm detected."
    else:
        score = "Low"
        description = "Natural phrasing with minimal detectable AI boilerplate."

    eliminated = []
    if rewritten_text:
        rewritten_lower = rewritten_text.lower()
        for c in cliches:
            if c.lower() not in rewritten_lower:
                eliminated.append(c)

    return {
        "detected_cliches": cliches,
        "cliche_count": cliche_count,
        "robotic_score": score,
        "sentence_variance": round(std_dev, 2),
        "sentence_count": num_sentences,
        "description": description,
        "eliminated_cliches": eliminated
    }
