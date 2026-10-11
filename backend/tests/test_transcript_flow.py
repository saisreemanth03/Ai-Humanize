import pytest
from app.utils.heuristic_humanizer import heuristic_humanize
from app.services.humanizer import humanize

def test_heuristic_transcript_cleanup():
    raw_text = """Look at him. He's perfect. [music] He has red, healthy, glowy skin. He's going to shine. Can I come, too? >> [crying] >> EXCELLENT WORK. >> [applause] >> I TRIED, TOO. WHY not me? >> [crying] >> I was never enough. If I turned red, would you finally see me?"""
    result = heuristic_humanize(raw_text, "Audio / Video Transcript & Spoken Dialogue", "Natural", False)
    assert "[music]" not in result["humanized_text"]
    assert "[crying]" not in result["humanized_text"]
    assert "[applause]" not in result["humanized_text"]
    assert ">>" not in result["humanized_text"]
    assert "EXCELLENT WORK" not in result["humanized_text"]
    assert "I TRIED, TOO" not in result["humanized_text"]

def test_live_or_mocked_transcript_flow():
    import os
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("No API key configured for live transcript test")
    raw_text = """Look at him. He's perfect. [music] He has red, healthy, glowy skin. He's going to shine. Can I come, too? >> [crying] >> EXCELLENT WORK. >> [applause] >> I TRIED, TOO. WHY not me? >> [crying] >> I was never enough. If I turned red, would you finally see me?"""
    result = humanize(raw_text, "Audio / Video Transcript & Spoken Dialogue", "Conversational", False)
    assert "humanized_text" in result
    assert len(result["humanized_text"]) > 20
