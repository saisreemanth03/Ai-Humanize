import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    HumanizeRequest,
    HumanizeResponse,
    AnalyzeRequest,
    RoboticAnalysis,
    YouTubeExtractRequest,
    MediaExtractResponse,
    ChatLinkExtractRequest,
    ChatLinkExtractResponse,
)
from app.services.humanizer import humanize, correct_missing_entities
from app.services.validator import validate, deterministic_validation_fallback
from app.services.document_extractor import extract_document, MAX_TEXT_CHARS
from app.services.media_extractor import extract_media_file, extract_youtube, MAX_MEDIA_BYTES
from app.services.chat_link_extractor import extract_chat_link
from app.utils.entity_checks import extract_entities, compare_entities, detailed_entity_audit
from app.utils.robotic_detector import analyze_robotic_language

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = FastAPI(title="HumanizeAI API", version="2.0.0")
origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin, "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ValueError)
async def value_error(_, exc):
    return __import__("fastapi").responses.JSONResponse(status_code=422, content={"detail": str(exc)})

@app.get("/")
def root():
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    return {"name": "HumanizeAI API", "status": "ok", "ai_configured": has_key, "track": "Problem Track 02 - Natural Language Refinement"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze-robotic")
@app.post("/api/analyze-robotic")
def analyze_robotic(req: AnalyzeRequest):
    """Analyze text for robotic phrasing clichés and sentence regularity."""
    text = req.text.strip()
    if not text:
        return RoboticAnalysis().dict()
    return analyze_robotic_language(text)

@app.post("/extract-document")
@app.post("/api/extract-document")
async def extract(file: UploadFile = File(...)):
    data = await file.read(5 * 1024 * 1024 + 1)
    try:
        return extract_document(file.filename or "upload", data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/extract-media")
@app.post("/api/extract-media")
async def extract_media(file: UploadFile = File(...)):
    data = await file.read(MAX_MEDIA_BYTES + 1)
    if len(data) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail="The media file exceeds the 25 MB upload limit.")
    try:
        return extract_media_file(file.filename or "media", data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/extract-youtube")
@app.post("/api/extract-youtube")
def extract_yt(req: YouTubeExtractRequest):
    try:
        return extract_youtube(req.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/fetch-ai-link", response_model=ChatLinkExtractResponse)
@app.post("/fetch-chat-link", response_model=ChatLinkExtractResponse)
@app.post("/api/fetch-ai-link", response_model=ChatLinkExtractResponse)
@app.post("/api/fetch-chat-link", response_model=ChatLinkExtractResponse)
async def fetch_chat_link(req: ChatLinkExtractRequest):
    try:
        return await extract_chat_link(req.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat link: {str(e)}")

@app.post("/humanize")
@app.post("/api/humanize")
def process(req: HumanizeRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Enter some text before humanizing.")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail="Text is limited to 20,000 characters.")

    # 1. Generation Pass: Humanize robotic text using selected context and tone
    try:
        result = humanize(
            text,
            req.context,
            req.tone,
            req.minimal_rewrite,
            api_key=req.api_key,
            provider=req.provider,
            model_override=req.model
        )
    except RuntimeError:
        # Fallback to local heuristic humanizer if server AI keys are unconfigured
        from app.utils.heuristic_humanizer import heuristic_humanize
        result = heuristic_humanize(text, req.context, req.tone, req.minimal_rewrite)
    except Exception as e:
        from openai import APITimeoutError, AuthenticationError, RateLimitError
        from app.utils.heuristic_humanizer import heuristic_humanize

        if isinstance(e, (TimeoutError, APITimeoutError)):
            result = heuristic_humanize(text, req.context, req.tone, req.minimal_rewrite)
            result.setdefault("warnings", []).append(
                "Upstream AI request timed out. Content was refined using the local natural language engine."
            )
        elif isinstance(e, AuthenticationError):
            if req.api_key:
                raise HTTPException(status_code=401, detail="Invalid AI API Key provided. Please verify your custom key.")
            result = heuristic_humanize(text, req.context, req.tone, req.minimal_rewrite)
            result.setdefault("warnings", []).append(
                "Upstream AI authentication failed. Content was refined using the local natural language engine."
            )
        elif isinstance(e, RateLimitError):
            if req.api_key:
                raise HTTPException(status_code=429, detail="Your custom API key quota or rate limit was reached.")
            result = heuristic_humanize(text, req.context, req.tone, req.minimal_rewrite)
            result.setdefault("warnings", []).append(
                "Upstream AI quota reached. Content was refined using the local natural language engine."
            )
        else:
            result = heuristic_humanize(text, req.context, req.tone, req.minimal_rewrite)

    # 2. Strict Entity & Terminology Guardrail: Audit entities & run correction pass if needed
    entity_audit = detailed_entity_audit(text, result["humanized_text"])
    if not entity_audit["is_100_percent_preserved"] and entity_audit["missing_entities"]:
        try:
            # Trigger automatic correction pass to re-integrate missing entities
            corrected = correct_missing_entities(
                original_text=text,
                rewritten_text=result["humanized_text"],
                missing_entities=entity_audit["missing_entities"],
                api_key=req.api_key,
                provider=req.provider,
                model_override=req.model
            )
            # Re-audit corrected output
            new_audit = detailed_entity_audit(text, corrected["humanized_text"])
            if len(new_audit["missing_entities"]) <= len(entity_audit["missing_entities"]):
                result["humanized_text"] = corrected["humanized_text"]
                entity_audit = new_audit
                if corrected.get("changes_summary"):
                    result["changes_summary"] = (result.get("changes_summary", "") + " " + corrected["changes_summary"]).strip()
        except Exception:
            # If correction pass fails, continue with initial rewrite and explicit warnings
            pass

    # 3. Robotic Language Analysis & Cliché Elimination
    robotic_report = analyze_robotic_language(text, result["humanized_text"])

    # 4. Warnings and Entity Checks
    raw_warnings = list(result.get("warnings", [])) + compare_entities(text, result["humanized_text"])
    result["extracted_entities"] = extract_entities(text)

    # 5. Verification Pass: Meaning Preservation & Verification Pipeline
    try:
        validation = validate(
            text,
            result["humanized_text"],
            api_key=req.api_key,
            provider=req.provider,
            model_override=req.model
        )
        meaning = {k: validation[k] for k in ("meaning_status", "meaning_explanation", "changed_facts", "added_claims", "omitted_claims", "review_warnings")}
        factuality = {k: validation[k] for k in ("factuality_status", "factuality_explanation", "changed_facts", "added_claims", "omitted_claims", "review_warnings")}
        raw_warnings.extend(validation.get("review_warnings", []))
    except Exception:
        fallback = deterministic_validation_fallback(text, result["humanized_text"], entity_audit["missing_entities"])
        meaning = {k: fallback[k] for k in ("meaning_status", "meaning_explanation", "changed_facts", "added_claims", "omitted_claims", "review_warnings")}
        factuality = {k: fallback[k] for k in ("factuality_status", "factuality_explanation", "changed_facts", "added_claims", "omitted_claims", "review_warnings")}
        validation = fallback
        raw_warnings.append("Independent validation could not run. Review important details yourself.")

    if raw_warnings:
        if meaning["meaning_status"] == "Passed":
            meaning["meaning_status"] = "Review recommended"
        if factuality["factuality_status"] == "Passed":
            factuality["factuality_status"] = "Review recommended"

    all_warnings = list(raw_warnings)
    all_warnings.append("Automated checks can miss errors and do not verify claims against external sources. Review important content.")

    # Calculate Problem Track 02 verification pipeline metrics
    meaning_preserved = bool(validation.get("meaning_preserved", True) and entity_audit["is_100_percent_preserved"])
    unsupported_claims_detected = bool(validation.get("unsupported_claims_detected", False) or bool(validation.get("added_claims", [])))
    
    factuality_conf = int(validation.get("factuality_confidence", 98))
    if not entity_audit["is_100_percent_preserved"]:
        factuality_conf = min(factuality_conf, int(entity_audit["preservation_rate"]))

    semantic_sim = int(validation.get("semantic_similarity_score", 95))

    return {
        "humanized_text": result["humanized_text"],
        "changes_summary": result.get("changes_summary", ""),
        "extracted_entities": result["extracted_entities"],
        "meaning_validation": meaning,
        "factuality_validation": factuality,
        "warnings": list(dict.fromkeys(all_warnings)),
        # Verification Pipeline exposed fields
        "meaning_preserved": meaning_preserved,
        "entities_preserved": entity_audit["entities_preserved"],
        "unsupported_claims_detected": unsupported_claims_detected,
        "factuality_confidence": factuality_conf,
        "preserved_terms": entity_audit["entities_preserved"],
        "semantic_similarity_score": semantic_sim,
        "robotic_analysis": robotic_report,
        "entity_guardrail": entity_audit
    }

@app.post("/api/humanize-document")
async def humanize_document(file: UploadFile = File(...), context: str = "General Professional Writing", tone: str = "Natural", minimal_rewrite: bool = False):
    from app.schemas import HumanizeRequest
    data = await file.read(5 * 1024 * 1024 + 1)
    try:
        extracted = extract_document(file.filename or "upload", data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        opts = HumanizeRequest(text=extracted["extracted_text"], context=context, tone=tone, minimal_rewrite=minimal_rewrite)
    except Exception as e:
        raise HTTPException(status_code=422, detail="Unsupported writing context or tone.") from e
    return {"extraction": extracted, "result": process(opts)}

@app.post("/api/humanize-media")
async def humanize_media(
    file: UploadFile = File(...),
    context: str = "General Professional Writing",
    tone: str = "Natural",
    minimal_rewrite: bool = False
):
    from app.schemas import HumanizeRequest
    data = await file.read(MAX_MEDIA_BYTES + 1)
    if len(data) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail="The media file exceeds the 25 MB upload limit.")
    try:
        extracted = extract_media_file(file.filename or "media", data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        opts = HumanizeRequest(text=extracted["extracted_text"], context=context, tone=tone, minimal_rewrite=minimal_rewrite)
    except Exception as e:
        raise HTTPException(status_code=422, detail="Unsupported writing context or tone.") from e
    return {"extraction": extracted, "result": process(opts)}

@app.post("/api/humanize-youtube")
def humanize_yt(
    req: YouTubeExtractRequest,
    context: str = "General Professional Writing",
    tone: str = "Natural",
    minimal_rewrite: bool = False
):
    from app.schemas import HumanizeRequest
    try:
        extracted = extract_youtube(req.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        opts = HumanizeRequest(text=extracted["extracted_text"], context=context, tone=tone, minimal_rewrite=minimal_rewrite)
    except Exception as e:
        raise HTTPException(status_code=422, detail="Unsupported writing context or tone.") from e
    return {"extraction": extracted, "result": process(opts)}

