import re
from typing import Any

# Numbers, percentages, currency, metrics
NUMBER_RE = re.compile(r"(?<!\w)(?:[$€£₹]\s*)?\d[\d,]*(?:\.\d+)?%?(?!\w)")
PERCENTAGE_RE = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*(?:%|percent\b)", re.I)
SCORE_RE = re.compile(r"(?<!\w)(?:\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?|(?:GPA\s*)?\d\.\d+(?:/\d\.\d+)?|score\s+(?:of\s+)?\d+(?:\.\d+)?)\b", re.I)

# Dates
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b|\b\d{4}-\d{2}-\d{2}\b)\b",
    re.I
)

# Common technical tools, frameworks, and programming stacks
TECH_TERMS = [
    "Python", "React", "React Native", "TypeScript", "JavaScript", "SQL", "NoSQL",
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "GraphQL", "Java", "C++",
    "C#", "Golang", "Go", "Rust", "Ruby", "Ruby on Rails", "Rails", "PHP", "Swift",
    "Kotlin", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Google Cloud",
    "Git", "GitHub", "GitLab", "Linux", "Jira", "Figma", "Node.js", "Node", "Next.js",
    "Vue", "Vue.js", "Angular", "Svelte", "FastAPI", "Django", "Flask", "Express",
    "Express.js", "Spring Boot", "Spring", "PyTorch", "TensorFlow", "Scikit-learn",
    "Pandas", "NumPy", "Kafka", "Spark", "Terraform", "Jenkins", "CI/CD", "REST API",
    "REST", "HTML", "CSS", "Tailwind", "TailwindCSS", "OpenAPI"
]

_TECH_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in sorted(TECH_TERMS, key=len, reverse=True)) + r")\b",
    re.I
)

def extract_entities(text: str) -> dict[str, Any]:
    """Extract numbers, dates, names, tech stacks, percentages, and metrics."""
    if not text:
        return {
            "names_and_capitalized_terms": [],
            "numbers": [],
            "dates": [],
            "technical_terms": [],
            "percentages": [],
            "scores_and_metrics": [],
            "all_critical_entities": []
        }

    numbers = list(dict.fromkeys(NUMBER_RE.findall(text)))
    dates = list(dict.fromkeys(DATE_RE.findall(text)))
    percentages = list(dict.fromkeys(PERCENTAGE_RE.findall(text)))
    scores = list(dict.fromkeys(SCORE_RE.findall(text)))
    
    # Technical stacks matching
    tech_matches = list(dict.fromkeys(_TECH_PATTERN.findall(text)))

    # Proper nouns and capitalized spans
    # Exclude common sentence starters, transitions, pronouns, and cliches
    non_entity_words = {
        "The", "This", "That", "These", "Those", "There", "Here", "We", "I", "You", "He", "She", "They",
        "It", "If", "When", "While", "In", "On", "At", "For", "To", "With", "After", "Before", "Please",
        "Thank", "Thanks", "Dear", "Hello", "Hi", "Furthermore", "Moreover", "Additionally", "However",
        "Therefore", "Meanwhile", "Nonetheless", "Nevertheless", "Consequently", "Similarly", "Specifically",
        "First", "Firstly", "Second", "Secondly", "Third", "Finally", "Lastly", "Overall", "Instead",
        "Indeed", "Certainly", "Naturally", "Clearly", "Obviously", "Notably", "Importantly", "Interestingly",
        "Surprisingly", "Ultimately", "Basically", "Essentially", "Generally", "Typically", "Usually",
        "Currently", "Recently", "Historically", "Initially", "Originally", "Already", "Still", "Again",
        "Also", "Besides", "Hence", "Thus", "Today", "Yesterday", "Tomorrow", "Now", "Then", "Delve",
        "Streamline", "Leverage", "Foster", "Pivotal", "Crucial", "Vital", "Game", "Beacon", "Tapestry",
        "Summary", "Conclusion", "Although", "Even", "Though", "Since", "Because", "As", "So", "Yet", "But",
        "And", "Or", "Nor", "Not", "Just", "Only", "Whether", "Whenever", "Wherever", "Whoever", "Whatever",
        "Why", "What", "Where", "Who", "Whom", "Whose", "How", "In today", "In todays", "It is", "There is",
        "There are", "By using", "Utilizing", "Using"
    }

    # Extract capitalized terms that appear mid-sentence (genuine proper nouns/names)
    mid_sentence_caps = re.findall(r"(?<=[a-zA-Z0-9,;:]\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text)
    filtered_names = []
    for item in mid_sentence_caps:
        words = item.split()
        if not all(w in non_entity_words for w in words) and item not in tech_matches:
            if item not in filtered_names:
                filtered_names.append(item)

    # Combine into all critical entities list
    all_critical = []
    for item in (tech_matches + scores + percentages + dates + filtered_names + numbers):
        clean_item = item.strip()
        if clean_item and clean_item not in all_critical:
            all_critical.append(clean_item)

    return {
        "names_and_capitalized_terms": filtered_names,
        "numbers": numbers,
        "dates": dates,
        "technical_terms": tech_matches,
        "percentages": percentages,
        "scores_and_metrics": scores,
        "all_critical_entities": all_critical
    }

def entity_present_in_text(entity: str, text: str) -> bool:
    """Check if an entity is present in text with boundary and normalization awareness."""
    if not entity or not text:
        return False
    # Exact substring check first
    if entity in text:
        return True
    # Case-insensitive boundary check
    escaped = re.escape(entity)
    if re.search(rf"\b{escaped}\b", text, re.I):
        return True
    # For numbers/percentages (e.g. "85 %" vs "85%")
    normalized_ent = re.sub(r"\s+", "", entity.lower())
    normalized_text = re.sub(r"\s+", "", text.lower())
    if normalized_ent in normalized_text:
        return True
    return False

def compare_entities(original: str, rewritten: str) -> list[str]:
    """Compare entities between original and rewritten text, returning human-friendly warnings."""
    orig_data = extract_entities(original)
    warnings = []

    # Check categories
    checks = [
        ("technical_terms", "technical tools or stacks"),
        ("numbers", "numbers or amounts"),
        ("dates", "dates"),
        ("percentages", "percentages"),
        ("scores_and_metrics", "test scores or metrics"),
        ("names_and_capitalized_terms", "names or capitalized terms")
    ]

    for key, label in checks:
        orig_items = orig_data.get(key, [])
        missing = [item for item in orig_items if not entity_present_in_text(item, rewritten)]
        if missing:
            warnings.append(f"Review {label} that may not have been preserved: {', '.join(missing)}")

    return warnings

def detailed_entity_audit(original: str, rewritten: str) -> dict[str, Any]:
    """Perform detailed verification of entity preservation."""
    orig_data = extract_entities(original)
    critical = orig_data["all_critical_entities"]
    
    preserved = [e for e in critical if entity_present_in_text(e, rewritten)]
    missing = [e for e in critical if e not in preserved]

    total = len(critical)
    preservation_rate = 100.0 if total == 0 else round((len(preserved) / total) * 100, 1)

    return {
        "all_entities": critical,
        "entities_preserved": preserved,
        "missing_entities": missing,
        "preservation_rate": preservation_rate,
        "is_100_percent_preserved": len(missing) == 0,
        "extracted_categories": orig_data
    }
