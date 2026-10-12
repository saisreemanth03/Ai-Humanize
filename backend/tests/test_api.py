import pytest
import json
from pydantic import ValidationError
from fastapi import HTTPException
from app import main
from app.main import health, process
from app.schemas import HumanizeRequest
from app.services.humanizer import humanize

class MemoryUpload:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content
    async def read(self, size: int = -1) -> bytes:
        return self.content[:size]

def upload_text(filename: str, content: bytes) -> MemoryUpload:
    return MemoryUpload(filename, content)

def run_immediate(coroutine):
    """Drive routes whose mocked upload read completes without external async I/O."""
    try:
        coroutine.send(None)
    except StopIteration as done:
        return done.value
    raise AssertionError("This isolated route test unexpectedly needed an event loop or external I/O.")

def test_health():
    assert health() == {"status":"ok"}

def test_empty_input_rejected():
    with pytest.raises(ValidationError):
        HumanizeRequest(text="")

def test_whitespace_input_rejected_by_route_contract():
    with pytest.raises(HTTPException) as exc:
        process(HumanizeRequest(text="   "))
    assert exc.value.status_code == 422

def test_unsupported_context_rejected():
    with pytest.raises(ValidationError):
        HumanizeRequest(text="A short sentence.", context="Unlisted context")

def test_missing_key_is_clear(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AI service is not configured"):
        humanize("A short sentence.", "General Writing", "Natural", False)

def test_humanize_workflow_with_mocked_independent_validator(monkeypatch):
    monkeypatch.setattr(main, "humanize", lambda text, context, tone, minimal, **kwargs: {
        "humanized_text": "Avery will deliver 12 reports on 10/12/2026.",
        "changes_summary": "Improved flow.", "warnings": []
    })
    monkeypatch.setattr(main, "validate", lambda original, rewritten, **kwargs: {
        "meaning_status": "Passed", "meaning_explanation": "The intent is consistent.",
        "factuality_status": "Passed", "factuality_explanation": "Key details are retained.",
        "changed_facts": [], "added_claims": [], "omitted_claims": [], "review_warnings": []
    })
    response = process(HumanizeRequest(text="Avery will deliver 12 reports on 10/12/2026."))
    assert response["humanized_text"].endswith("10/12/2026.")
    assert response["meaning_validation"]["meaning_status"] == "Passed"
    assert response["factuality_validation"]["factuality_status"] == "Passed"
    assert "12" in response["extracted_entities"]["numbers"]

def test_validator_failure_is_reported_honestly(monkeypatch):
    monkeypatch.setattr(main, "humanize", lambda *args, **kwargs: {
        "humanized_text": "A clearer sentence.", "changes_summary": "Reworded.", "warnings": []
    })
    def unavailable(*args, **kwargs): raise RuntimeError("provider unavailable")
    monkeypatch.setattr(main, "validate", unavailable)
    response = process(HumanizeRequest(text="A sentence."))
    assert response["meaning_validation"]["meaning_status"] == "Review recommended"
    assert any("validation could not run" in warning for warning in response["warnings"])

def test_document_upload_endpoint_extracts_txt():
    upload = upload_text("note.txt", b"A real upload endpoint test.")
    result = run_immediate(main.extract(upload))
    assert result["filename"] == "note.txt"
    assert result["extracted_text"] == "A real upload endpoint test."

def test_humanize_document_workflow_with_mocked_ai(monkeypatch):
    monkeypatch.setattr(main, "humanize", lambda text, context, tone, minimal, **kwargs: {
        "humanized_text": "A refined upload sentence.", "changes_summary": "Smoothed flow.", "warnings": []
    })
    monkeypatch.setattr(main, "validate", lambda original, rewritten, **kwargs: {
        "meaning_status": "Review recommended", "meaning_explanation": "Review source.",
        "factuality_status": "Review recommended", "factuality_explanation": "Review source.",
        "changed_facts": [], "added_claims": [], "omitted_claims": [], "review_warnings": []
    })
    upload = upload_text("note.txt", b"Original upload sentence.")
    response = run_immediate(main.humanize_document(upload, "General Writing", "Natural", False))
    assert response["extraction"]["extracted_text"] == "Original upload sentence."
    assert response["result"]["humanized_text"] == "A refined upload sentence."

def test_ai_client_response_json_is_parsed_with_mock(monkeypatch):
    from app.services import ai_client, humanizer
    payload = {"humanized_text":"Natural wording.","changes_summary":"Adjusted flow.","robotic_signals":[],"uncertain_edits":[],"warnings":[]}
    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["response_format"] == {"type":"json_object"}
            return type("Response", (), {"choices":[type("Choice", (), {"message":type("Message", (), {"content":json.dumps(payload)})()})()]})()
    class FakeClient:
        def __init__(self, **kwargs): self.chat=type("Chat", (), {"completions":FakeCompletions()})()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_client, "OpenAI", FakeClient)
    assert humanizer.humanize("Original wording.", "General Writing", "Natural", False)["humanized_text"] == "Natural wording."

def test_malformed_ai_json_is_rejected():
    from app.services.humanizer import _json_object
    with pytest.raises(ValueError, match="unreadable"):
        _json_object("not JSON")

def test_ai_json_with_wrong_field_types_is_rejected():
    from app.services.humanizer import _json_object
    with pytest.raises(ValueError, match="warnings list"):
        _json_object(json.dumps({"humanized_text":"Text.","warnings":"not a list"}))

def test_timeout_falls_back_gracefully_to_heuristic(monkeypatch):
    from openai import APITimeoutError
    import httpx
    fake_request = httpx.Request("POST", "https://generativelanguage.googleapis.com")
    def fake_humanize_timeout(*args, **kwargs):
        raise APITimeoutError(fake_request)
    monkeypatch.setattr(main, "humanize", fake_humanize_timeout)
    monkeypatch.setattr(main, "validate", lambda *args, **kwargs: {
        "meaning_status": "Passed", "meaning_preserved": True,
        "factuality_status": "Passed", "factuality_confidence": 95,
        "semantic_similarity_score": 92, "unsupported_claims_detected": False,
        "changed_facts": [], "added_claims": [], "omitted_claims": [], "review_warnings": []
    })
    response = main.process(HumanizeRequest(text="Furthermore, it is imperative to delve into the matter."))
    assert "humanized_text" in response
    assert response["humanized_text"] != ""
    assert any("timed out" in w.lower() for w in response["warnings"])
