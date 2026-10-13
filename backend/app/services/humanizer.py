import json
from typing import Optional
from app.prompts import SYSTEM_PROMPT, CORRECTION_PROMPT
from app.services.ai_client import get_ai_client

def _json_object(content: str) -> dict:
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("The AI returned an unreadable response.")
        obj = json.loads(content[start:end+1])
    if not isinstance(obj, dict) or not isinstance(obj.get("humanized_text"), str) or not obj["humanized_text"].strip():
        raise ValueError("The AI response did not contain usable rewritten text.")
    obj.setdefault("changes_summary", "")
    if not isinstance(obj["changes_summary"], str):
        raise ValueError("The AI response contained an invalid changes summary.")
    for key in ("robotic_signals", "uncertain_edits", "warnings"):
        obj.setdefault(key, [])
        if not isinstance(obj[key], list) or any(not isinstance(item, str) for item in obj[key]):
            raise ValueError(f"The AI response contained an invalid {key} list.")
    return obj

def humanize(
    text: str,
    context: str,
    tone: str,
    minimal_rewrite: bool,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model_override: Optional[str] = None
) -> dict:
    client, model = get_ai_client(custom_api_key=api_key, custom_provider=provider, custom_model=model_override)
    
    rewrite_mode_str = (
        "Minimal Surgical Rewrite: Preserve original sentence structure, length, and boundaries strictly. Only replace robotic cliches and awkward words."
        if minimal_rewrite else
        "Full Dynamic Humanization: Actively restructure robotic sentences, vary pacing and cadence, and eliminate formulaic AI patterns into natural human voice."
    )

    user_prompt = f"""Tone Preset: {tone}
Rewrite Mode: {rewrite_mode_str}
Domain Context: {context}

Original Text to Refine:
\"\"\"{text}\"\"\"

Task Requirements:
1. Apply the '{tone}' tone preset distinctly as detailed in the guidelines.
2. Adhere strictly to the '{('Minimal Surgical Rewrite' if minimal_rewrite else 'Full Dynamic Humanization')}' mode.
3. Eliminate robotic cliches and formulaic AI sentence starters.
4. Strictly preserve all facts, numbers, dates, test scores, metrics, and technical terms.
5. If the input contains audio/video transcription noise, closed-caption markers (such as [music], [crying], [applause], [laughter], '>>' speaker markers, or ALL-CAPS shouting), convert them into clean, natural human dialogue or prose with authentic flow and cadence.
6. Return valid compact JSON only with keys: humanized_text, changes_summary.
"""

    candidate_models = [model]
    if not model_override and not api_key and ("gemini" in model.lower() or "flash" in model.lower()):
        for backup in ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]:
            if backup not in candidate_models:
                candidate_models.append(backup)

    last_exc = None
    for candidate in candidate_models:
        try:
            response = client.chat.completions.create(
                model=candidate,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
            )
            content = response.choices[0].message.content or ""
            return _json_object(content)
        except Exception as e:
            last_exc = e
            from openai import RateLimitError, NotFoundError, APITimeoutError, APIConnectionError, InternalServerError
            if isinstance(e, (RateLimitError, NotFoundError, APITimeoutError, TimeoutError, APIConnectionError, InternalServerError)) and candidate != candidate_models[-1]:
                continue
            raise e

    if last_exc:
        raise last_exc


def correct_missing_entities(
    original_text: str,
    rewritten_text: str,
    missing_entities: list[str],
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model_override: Optional[str] = None
) -> dict:
    """Correction pass to re-incorporate missing critical entities into rewritten text."""
    if not missing_entities:
        return {"humanized_text": rewritten_text, "changes_summary": "No entities missing."}
    client, model = get_ai_client(custom_api_key=api_key, custom_provider=provider, custom_model=model_override)
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": CORRECTION_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "original_text": original_text,
                    "rewritten_text": rewritten_text,
                    "missing_entities_to_restore": missing_entities
                }, ensure_ascii=False)
            }
        ]
    )
    content = response.choices[0].message.content or ""
    return _json_object(content)
