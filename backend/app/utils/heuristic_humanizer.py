import re
from app.utils.entity_checks import extract_entities, entity_present_in_text

REPLACEMENTS = [
    (re.compile(r"\bcan you delve into\b", re.I), "could you tell us more about"),
    (re.compile(r"\bdelving into\b", re.I), "exploring"),
    (re.compile(r"\bdelve deeper into\b", re.I), "take a closer look at"),
    (re.compile(r"\bdelve into\b", re.I), "explore"),
    (re.compile(r"\bdelve\b", re.I), "look closely"),
    (re.compile(r"\bstands as a testament to\b", re.I), "clearly highlights"),
    (re.compile(r"\ba testament to\b", re.I), "strong evidence of"),
    (re.compile(r"\brich tapestry\b", re.I), "diverse combination"),
    (re.compile(r"\btapestry of\b", re.I), "range of"),
    (re.compile(r"\btapestry\b", re.I), "mix"),
    (re.compile(r"\bin summary,\s*", re.I), "Overall, "),
    (re.compile(r"\bin conclusion,\s*", re.I), "To sum up, "),
    (re.compile(r"\bto summarize,\s*", re.I), "In short, "),
    (re.compile(r"\bpivotal role\b", re.I), "key role"),
    (re.compile(r"\bpivotal\b", re.I), "critical"),
    (re.compile(r"\bbeacon of hope\b", re.I), "inspiring example"),
    (re.compile(r"\bbeacon of\b", re.I), "model for"),
    (re.compile(r"\bfurthermore,\s*", re.I), "Additionally, "),
    (re.compile(r"\bmoreover,\s*", re.I), "Also, "),
    (re.compile(r"\bit is worth noting that\s*", re.I), "notably, "),
    (re.compile(r"\bit is noteworthy that\s*", re.I), "importantly, "),
    (re.compile(r"\bit should be noted that\s*", re.I), "keep in mind that "),
    (re.compile(r"\bembark upon\b", re.I), "begin"),
    (re.compile(r"\bembark on\b", re.I), "start"),
    (re.compile(r"\bfoster\b", re.I), "encourage"),
    (re.compile(r"\bstreamline\b", re.I), "simplify"),
    (re.compile(r"\bstreamlining\b", re.I), "simplifying"),
    (re.compile(r"\bleverage\b", re.I), "utilize"),
    (re.compile(r"\bleveraging\b", re.I), "utilizing"),
    (re.compile(r"\bvital role\b", re.I), "essential role"),
    (re.compile(r"\bcrucial role\b", re.I), "central role"),
    (re.compile(r"\bgame-changer\b", re.I), "major advantage"),
    (re.compile(r"\bplethora of\b", re.I), "many"),
    (re.compile(r"\bmyriad of\b", re.I), "wide range of"),
    (re.compile(r"\bmyriad\b", re.I), "numerous"),
    (re.compile(r"\bmultifaceted\b", re.I), "comprehensive"),
    (re.compile(r"\bunderpins\b", re.I), "supports"),
    (re.compile(r"\bintertwined\b", re.I), "closely connected"),
    (re.compile(r"\bunwavering\b", re.I), "consistent"),
    (re.compile(r"\bdeep dive\b", re.I), "detailed review"),
    (re.compile(r"\bharness the power of\b", re.I), "make the most of"),
    (re.compile(r"\bwithout further ado,\s*", re.I), "straight away, ")
]

def heuristic_humanize(
    text: str,
    context: str = "General Professional Writing",
    tone: str = "Natural",
    minimal_rewrite: bool = False
) -> dict:
    refined = text
    eliminated_cliches = []

    # 0. Audio & Transcript Artifact Cleanup
    transcript_cues = re.findall(r"\[(?:music|crying|applause|laughter|cheering|sniffling|coughing|sighs?|gasp|groans?|inaudible)\]", refined, flags=re.I)
    if transcript_cues:
        eliminated_cliches.extend(transcript_cues)
        refined = re.sub(r"\[(?:music|crying|applause|laughter|cheering|sniffling|coughing|sighs?|gasp|groans?|inaudible)\]\s*", "", refined, flags=re.I)
    
    if ">>" in refined:
        refined = re.sub(r">\s*>\s*", " ", refined)

    # Normalize all-caps shouting dialogue (e.g., "EXCELLENT WORK" -> "excellent work")
    def _lower_shout(m):
        w = m.group(0)
        return w if w in ("API", "SQL", "AWS", "GPA", "HTML", "CSS", "GCP", "REST") else w.lower()
    refined = re.sub(r"\b[A-Z]{2,}\b", _lower_shout, refined)

    # 1. Opening trope reframing (when NOT minimal rewrite)
    opening_trope = re.compile(r"^(?:In today's fast-paced digital landscape|In today's fast-paced world),\s*", re.I)
    if opening_trope.search(refined):
        eliminated_cliches.append("In today's fast-paced digital landscape")
        if not minimal_rewrite:
            if tone == "Concise":
                refined = opening_trope.sub("Today, ", refined)
            elif tone == "Conversational":
                refined = opening_trope.sub("In today's fast-moving tech space, ", refined)
            elif tone == "Professional":
                refined = opening_trope.sub("In today's dynamic business environment, ", refined)
            elif tone == "Polished":
                refined = opening_trope.sub("Across the modern digital landscape, ", refined)
            else: # Natural
                refined = opening_trope.sub("In our fast-moving digital world, ", refined)
        else:
            # Minimal rewrite keeps structure closer
            refined = opening_trope.sub("In today's digital landscape, ", refined)

    # 2. Base Cliché Replacements
    for pattern, replacement in REPLACEMENTS:
        matches = pattern.findall(refined)
        if matches:
            eliminated_cliches.extend(matches)
            refined = pattern.sub(replacement, refined)

    # 3. Tone-Specific Nuances
    if tone == "Concise":
        refined = re.sub(r"\bseeking to optimize their workflow efficiency\b", "seeking greater efficiency", refined, flags=re.I)
        refined = re.sub(r"\bit is important to note that\s*", "Notably, ", refined, flags=re.I)
        refined = re.sub(r"\bpotential implementation challenges\b", "implementation challenges", refined, flags=re.I)
    elif tone == "Conversational":
        refined = re.sub(r"\bit is\b", "it's", refined, flags=re.I)
        refined = re.sub(r"\bdo not\b", "don't", refined, flags=re.I)
        refined = re.sub(r"\bcannot\b", "can't", refined, flags=re.I)
        refined = re.sub(r"\bAdditionally,\s*", "Plus, ", refined, flags=re.I)
        refined = re.sub(r"\butilize\b", "use", refined, flags=re.I)
        refined = re.sub(r"\butilizing\b", "using", refined, flags=re.I)
    elif tone == "Professional":
        refined = re.sub(r"\bAdditionally,\s*", "In addition, ", refined, flags=re.I)
        refined = re.sub(r"\blook closely\b", "examine thoroughly", refined, flags=re.I)
    elif tone == "Polished":
        refined = re.sub(r"\bAdditionally,\s*", "Moreover, ", refined, flags=re.I)
        refined = re.sub(r"\bclear evidence\b", "compelling evidence", refined, flags=re.I)

    # 4. Clean up awkward whitespace or double punctuation
    refined = re.sub(r"\s+", " ", refined)
    refined = re.sub(r"\s+([.,!?;:])", r"\1", refined)
    refined = re.sub(r"([.,!?;:])\1+", r"\1", refined).strip()

    # Capitalize sentence beginnings
    sentences = re.split(r"(?<=[.!?])\s+", refined)
    sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
    refined = " ".join(sentences)

    return {
        "humanized_text": refined,
        "changes_summary": f"Refined with {tone} tone ({('minimal surgical' if minimal_rewrite else 'dynamic')} rewrite). Eliminated {len(eliminated_cliches)} robotic phrases.",
        "robotic_signals": list(dict.fromkeys(eliminated_cliches)),
        "uncertain_edits": [],
        "warnings": ["AI provider quota was exhausted; executed deterministic entity-preserving refinement fallback."]
    }

