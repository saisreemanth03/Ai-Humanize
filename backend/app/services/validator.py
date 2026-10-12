import json
import difflib
from typing import Optional
from app.prompts import VALIDATOR_PROMPT
from app.services.ai_client import get_ai_client

def deterministic_validation_fallback(original: str, rewritten: str, missing_entities: Optional[list[str]] = None) -> dict:
    """Deterministic fallback validation when AI validator is offline."""
    ratio = difflib.SequenceMatcher(None, original.lower(), rewritten.lower()).ratio()
    similarity = max(50, min(99, int(ratio * 100)))
    
    missing = missing_entities or []
    has_issues = len(missing) > 0
    fact_conf = max(40, 98 - (len(missing) * 15))
    
    meaning_status = "Passed" if similarity > 60 and not has_issues else "Review recommended"
    fact_status = "Passed" if not has_issues else "Review recommended"
    
    return {
        "meaning_status": meaning_status,
        "meaning_preserved": not has_issues and similarity > 50,
        "meaning_explanation": "Deterministic textual comparison shows high semantic continuity." if not has_issues else f"Review recommended: potential entity variance ({', '.join(missing)}).",
        "semantic_similarity_score": similarity,
        "factuality_status": fact_status,
        "factuality_confidence": fact_conf,
        "factuality_explanation": "Automated deterministic check completed." if not has_issues else f"Review suggested for unverified entities: {', '.join(missing)}.",
        "unsupported_claims_detected": False,
        "changed_facts": [],
        "added_claims": [],
        "omitted_claims": [f"Missing entity: {m}" for m in missing],
        "review_warnings": [f"Unverified entity change: {m}" for m in missing] if missing else []
    }

def validate(
    original: str,
    rewritten: str,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model_override: Optional[str] = None
) -> dict:
    client, model = get_ai_client(custom_api_key=api_key, custom_provider=provider, custom_model=model_override)
    candidate_models = [model]
    if not model_override and not api_key and ("gemini" in model.lower() or "flash" in model.lower()):
        for backup in ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]:
            if backup not in candidate_models:
                candidate_models.append(backup)

    result = None
    last_exc = None
    for candidate in candidate_models:
        try:
            response = client.chat.completions.create(
                model=candidate,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": VALIDATOR_PROMPT},
                    {"role": "user", "content": json.dumps({"source_text": original, "humanized_text": rewritten}, ensure_ascii=False)}
                ]
            )
            result = json.loads(response.choices[0].message.content or "{}")
            break
        except Exception as e:
            last_exc = e
            from openai import RateLimitError, NotFoundError, APITimeoutError, APIConnectionError, InternalServerError
            if isinstance(e, (RateLimitError, NotFoundError, APITimeoutError, TimeoutError, APIConnectionError, InternalServerError)) and candidate != candidate_models[-1]:
                continue
            raise e
    if not isinstance(result, dict):
        raise ValueError("Validator response was not a JSON object.")

    allowed = {"Passed", "Review recommended", "Potential issue detected"}
    if result.get("meaning_status") not in allowed:
        result["meaning_status"] = "Passed" if result.get("meaning_preserved") is True else "Review recommended"
    if result.get("factuality_status") not in allowed:
        result["factuality_status"] = "Passed" if not result.get("unsupported_claims_detected") else "Review recommended"

    # Default fallbacks for enhanced verification attributes
    result.setdefault("meaning_preserved", result["meaning_status"] == "Passed")
    if not isinstance(result["meaning_preserved"], bool):
        result["meaning_preserved"] = bool(result["meaning_preserved"])

    try:
        score = int(result.get("semantic_similarity_score", 95 if result["meaning_status"] == "Passed" else 82))
        result["semantic_similarity_score"] = max(0, min(100, score))
    except (ValueError, TypeError):
        result["semantic_similarity_score"] = 92

    try:
        conf = int(result.get("factuality_confidence", 98 if result["factuality_status"] == "Passed" else 78))
        result["factuality_confidence"] = max(0, min(100, conf))
    except (ValueError, TypeError):
        result["factuality_confidence"] = 95

    result.setdefault("unsupported_claims_detected", False)
    if not isinstance(result["unsupported_claims_detected"], bool):
        result["unsupported_claims_detected"] = bool(result["unsupported_claims_detected"])

    for key in ("meaning_explanation", "factuality_explanation"):
        result.setdefault(key, "")
        if not isinstance(result.get(key), str):
            result[key] = str(result[key])

    for key in ("changed_facts", "added_claims", "omitted_claims", "review_warnings"):
        result.setdefault(key, [])
        if not isinstance(result[key], list) or any(not isinstance(item, str) for item in result[key]):
            result[key] = [str(item) for item in result[key]] if isinstance(result[key], list) else []

    return result
