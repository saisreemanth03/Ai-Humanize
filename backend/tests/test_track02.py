import pytest
from app.utils.robotic_detector import detect_robotic_phrases, analyze_robotic_language
from app.utils.entity_checks import extract_entities, detailed_entity_audit, entity_present_in_text
from app.schemas import HumanizeRequest
from app import main

def test_robotic_cliche_detection():
    sample = "Can you delve into this? It stands as a testament to our rich tapestry. Furthermore, it is worth noting the results."
    cliches = detect_robotic_phrases(sample)
    assert any("delve" in c.lower() for c in cliches)
    assert any("testament" in c.lower() for c in cliches)
    assert any("tapestry" in c.lower() for c in cliches)
    assert any("worth noting" in c.lower() for c in cliches)

def test_robotic_language_score():
    robotic_sample = "Can you delve into the project? Furthermore, it stands as a testament to our team. It is worth noting that we streamline processes."
    analysis = analyze_robotic_language(robotic_sample)
    assert analysis["robotic_score"] in ["High", "Medium"]
    assert len(analysis["detected_cliches"]) >= 3

    clean_sample = "We reviewed Sarah's resume. She built the React frontend and wrote clean Python code for the backend."
    clean_analysis = analyze_robotic_language(clean_sample)
    assert clean_analysis["robotic_score"] == "Low"

def test_robotic_elimination_tracking():
    orig = "Can you delve into why this is a testament to our success?"
    rewritten = "Could you explain why this demonstrates our success?"
    analysis = analyze_robotic_language(orig, rewritten)
    assert len(analysis["eliminated_cliches"]) >= 1

def test_entity_extraction_for_recruitment_and_tech():
    text = "Candidate Sarah Connor scored 95/100 on the assessment with an 85% accuracy rate. She is proficient in Python, React, and SQL. Interview scheduled for Oct 11, 2026."
    entities = extract_entities(text)
    
    # Tech stack
    assert "Python" in entities["technical_terms"]
    assert "React" in entities["technical_terms"]
    assert "SQL" in entities["technical_terms"]
    
    # Percentages and scores
    assert any("85" in p for p in entities["percentages"])
    assert any("95" in s for s in entities["scores_and_metrics"])
    
    # Dates
    assert any("Oct 11" in d or "2026" in d for d in entities["dates"])

def test_detailed_entity_audit_and_preservation():
    orig = "John scored 92% in the React and Python coding challenge on Oct 11."
    good_rewrite = "On Oct 11, John achieved a 92% score on the Python and React challenge."
    bad_rewrite = "The candidate did well on the web development challenge recently."
    
    audit_good = detailed_entity_audit(orig, good_rewrite)
    assert audit_good["is_100_percent_preserved"] is True
    assert audit_good["preservation_rate"] == 100.0

    audit_bad = detailed_entity_audit(orig, bad_rewrite)
    assert audit_bad["is_100_percent_preserved"] is False
    assert len(audit_bad["missing_entities"]) > 0

def test_recruitment_contexts_accepted():
    contexts = [
        "Recruiter Feedback & Rejection Emails",
        "Candidate Communication & Offer Letters",
        "Adaptive Interview Question Refinement",
        "Candidate Evaluation Summaries & Reports",
        "General Professional Writing"
    ]
    for ctx in contexts:
        req = HumanizeRequest(text="John excels with Python and SQL.", context=ctx)
        assert req.context == ctx

def test_verification_pipeline_response_fields(monkeypatch):
    sample_text = "John scored 95% in the Python assessment on Oct 12."
    monkeypatch.setattr(main, "humanize", lambda text, context, tone, minimal, **kwargs: {
        "humanized_text": "John scored 95% in the Python assessment on Oct 12.",
        "changes_summary": "Polished phrasing.",
        "warnings": []
    })
    monkeypatch.setattr(main, "validate", lambda original, rewritten, **kwargs: {
        "meaning_status": "Passed",
        "meaning_preserved": True,
        "meaning_explanation": "Intent is completely retained.",
        "semantic_similarity_score": 98,
        "factuality_status": "Passed",
        "factuality_confidence": 99,
        "factuality_explanation": "All numbers and terms preserved.",
        "unsupported_claims_detected": False,
        "changed_facts": [],
        "added_claims": [],
        "omitted_claims": [],
        "review_warnings": []
    })

    req = HumanizeRequest(text=sample_text, context="Candidate Evaluation Summaries & Reports")
    res = main.process(req)
    
    assert res["meaning_preserved"] is True
    assert "Python" in res["entities_preserved"]
    assert res["unsupported_claims_detected"] is False
    assert res["factuality_confidence"] >= 90
    assert res["semantic_similarity_score"] >= 90
    assert "robotic_analysis" in res
    assert "entity_guardrail" in res
