import json
import asyncio
from typing import Optional, AsyncGenerator
from app.prompts import SYSTEM_PROMPT, CORRECTION_PROMPT, STREAM_SYSTEM_PROMPT
from app.services.ai_client import get_ai_client, get_async_ai_client

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

import os
import httpx

def _get_gemini_key(custom_key: Optional[str] = None) -> Optional[str]:
    return custom_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

def _direct_gemini_humanize(
    prompt: str,
    system_prompt: str,
    api_key: str,
    model: str = "gemini-2.5-flash"
) -> dict:
    """Direct high-speed Google REST API call bypassing proxy overhead and thinking delay (<2s)."""
    clean_model = model if "gemini" in model.lower() else "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _json_object(raw_text)

async def _direct_gemini_stream(
    prompt: str,
    system_prompt: str,
    api_key: str,
    model: str = "gemini-2.5-flash"
) -> AsyncGenerator[str, None]:
    """Direct high-speed SSE token streaming with zero thinking delay (TTFT ~1.4s)."""
    clean_model = model if "gemini" in model.lower() else "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:streamGenerateContent?alt=sse&key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingBudget": 0},
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    raw_data = line[5:].strip()
                    if not raw_data:
                        continue
                    try:
                        parsed = json.loads(raw_data)
                        candidates = parsed.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            for part in candidates[0]["content"].get("parts", []):
                                txt = part.get("text", "")
                                if txt:
                                    yield txt
                    except Exception:
                        pass

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
    is_gemini_model = "gemini" in model.lower() or "flash" in model.lower()

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

    # 1. Fast-path: Direct Google Gemini REST (<2s latency) when model is Gemini
    gem_key = _get_gemini_key(api_key if provider != "openai" else None)
    if is_gemini_model and gem_key and provider != "openai":
        try:
            return _direct_gemini_humanize(
                prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT,
                api_key=gem_key,
                model=model
            )
        except Exception:
            pass

    # 2. Secondary path: OpenAI client abstraction
    candidate_models = [model]
    if not model_override and not api_key and is_gemini_model:
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


async def humanize_stream(
    text: str,
    context: str,
    tone: str,
    minimal_rewrite: bool,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model_override: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """Streams rewritten humanized text token-by-token directly from LLM in <1.5s."""
    try:
        client, model = get_async_ai_client(custom_api_key=api_key, custom_provider=provider, custom_model=model_override)
    except Exception:
        from app.utils.heuristic_humanizer import heuristic_humanize
        res = heuristic_humanize(text, context, tone, minimal_rewrite)
        words = res["humanized_text"].split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.005)
        return

    is_gemini_model = "gemini" in model.lower() or "flash" in model.lower()

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

Task:
Refine the original text into natural human voice adhering strictly to the '{tone}' tone preset and the '{rewrite_mode_str}'. Preserve 100% of all numbers, entities, metrics, dates, and technical tools. Output ONLY the refined human text directly.
"""

    # 1. Fast-path: Direct Google Gemini SSE streaming (<1.5s TTFT)
    gem_key = _get_gemini_key(api_key if provider != "openai" else None)
    if is_gemini_model and gem_key and provider != "openai":
        streamed_any = False
        try:
            async for chunk in _direct_gemini_stream(
                prompt=user_prompt,
                system_prompt=STREAM_SYSTEM_PROMPT,
                api_key=gem_key,
                model=model
            ):
                streamed_any = True
                yield chunk
            if streamed_any:
                return
        except Exception:
            if streamed_any:
                return

    candidate_models = [model]
    if not model_override and not api_key and ("gemini" in model.lower() or "flash" in model.lower()):
        for backup in ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]:
            if backup not in candidate_models:
                candidate_models.append(backup)

    stream_started = False
    for candidate in candidate_models:
        try:
            response = await client.chat.completions.create(
                model=candidate,
                stream=True,
                messages=[
                    {"role": "system", "content": STREAM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
                if delta:
                    stream_started = True
                    yield delta
            return
        except Exception:
            if not stream_started and candidate != candidate_models[-1]:
                continue
            break

    # If all candidates failed or timed out before streaming, fallback to local heuristic
    if not stream_started:
        from app.utils.heuristic_humanizer import heuristic_humanize
        res = heuristic_humanize(text, context, tone, minimal_rewrite)
        words = res["humanized_text"].split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.005)
        return


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
