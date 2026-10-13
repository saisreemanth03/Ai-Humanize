import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.chat_link_extractor import (
    validate_any_http_url,
    extract_bulk_inner_text,
    extract_chat_link,
    is_antibot_or_junk,
    clean_extracted_text,
    attempt_jina_reader,
    attempt_scraper_api,
    attempt_direct_ssr,
)

client = TestClient(app)

MOCK_CHATGPT_SSR_HTML = """
<!DOCTYPE html>
<html>
<head><title>Shared ChatGPT</title></head>
<body>
  <script id="__NEXT_DATA__" type="application/json">
  {
    "props": {
      "pageProps": {
        "sharedConversation": {
          "mapping": {
            "node-1": {
              "message": {
                "author": { "role": "user" },
                "content": { "parts": ["Please evaluate candidate John Doe."] }
              }
            },
            "node-2": {
              "message": {
                "author": { "role": "assistant" },
                "content": { "parts": ["John Doe demonstrates stellar competencies in Python and React. His technical leadership on Project Titan delivered a 40% latency reduction."] }
              }
            }
          }
        }
      }
    }
  }
  </script>
</body>
</html>
"""

MOCK_CLAUDE_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Claude Artifact</title></head>
<body>
  <nav><button>Sign In</button></nav>
  <main>
    <h1>Project Retrospective</h1>
    <p>Claude: The candidate demonstrated profound systems architecture skills, migrating legacy monoliths to event-driven architectures.</p>
  </main>
  <footer><p>Anthropic 2026</p></footer>
</body>
</html>
"""

MOCK_GENERIC_WEB_HTML = """
<!DOCTYPE html>
<html>
<body>
  <nav>Menu</nav>
  <div class="content">
    <p>This is a candidate evaluation summary extracted from an external applicant tracking system.</p>
    <p>Key qualifications include 5 years of full stack Python engineering and high scalability design.</p>
  </div>
  <footer>Copyright 2026</footer>
</body>
</html>
"""


def test_universal_url_validation():
    # Accepts any valid HTTP/HTTPS URL
    assert validate_any_http_url("https://chatgpt.com/s/t_6accd63oc23c81919386dff87e73c8f4") == "ChatGPT"
    assert validate_any_http_url("https://chatgpt.com/share/abc-123") == "ChatGPT"
    assert validate_any_http_url("https://gemini.google.com/share/9876543210ab") == "Gemini"
    assert validate_any_http_url("https://share.gemini.google/JNQrDtl4uXmO") == "Gemini"
    assert validate_any_http_url("https://claude.ai/chat/12345-abcde") == "Claude"
    assert validate_any_http_url("https://perplexity.ai/search/12345") == "Perplexity"
    assert validate_any_http_url("https://deepseek.com/chat/xyz") == "DeepSeek"
    assert validate_any_http_url("https://example.com/shared/notes") == "example.com"


def test_gemini_private_app_link_rejected_with_guidance():
    with pytest.raises(ValueError, match="private Gemini chat URL"):
        validate_any_http_url("https://gemini.google.com/app/1708968e8cca986b")


def test_url_validation_rejection_for_non_http():
    with pytest.raises(ValueError, match="Invalid URL format"):
        validate_any_http_url("ftp://example.com/file")

    with pytest.raises(ValueError, match="Invalid URL format"):
        validate_any_http_url("javascript:alert(1)")

    with pytest.raises(ValueError, match="valid URL string"):
        validate_any_http_url("")


def test_gemini_signin_shell_rejected():
    shell_html = "<html><body><div>Gemini - direct access to Google AI</div><div>Sign in</div><div>Google apps</div></body></html>"
    text = extract_bulk_inner_text(shell_html)
    assert text == ""


def test_extract_bulk_inner_text_ssr():
    text = extract_bulk_inner_text(MOCK_CHATGPT_SSR_HTML)
    assert "John Doe demonstrates stellar competencies" in text


def test_extract_bulk_inner_text_claude():
    text = extract_bulk_inner_text(MOCK_CLAUDE_PAGE_HTML)
    assert "Project Retrospective" in text
    assert "migrating legacy monoliths" in text
    # Ensure footer/nav is stripped
    assert "Sign In" not in text
    assert "Anthropic 2026" not in text


def test_extract_bulk_inner_text_generic_web():
    text = extract_bulk_inner_text(MOCK_GENERIC_WEB_HTML)
    assert "candidate evaluation summary" in text
    assert "high scalability design" in text
    assert "Menu" not in text


@pytest.mark.anyio
async def test_extract_chat_link_universal_success():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.url = "https://claude.ai/chat/12345"
        mock_response.text = MOCK_CLAUDE_PAGE_HTML
        mock_get.return_value = mock_response

        res = await extract_chat_link("https://claude.ai/chat/12345")
        assert res["platform"] == "Claude"
        assert "migrating legacy monoliths" in res["extracted_text"]
        assert res["word_count"] > 5


def test_api_fetch_chat_link_endpoint():
    with patch("app.main.extract_chat_link", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = {
            "platform": "Claude",
            "url": "https://claude.ai/share/123",
            "extracted_text": "Claude generated candidate evaluation notes.",
            "word_count": 5,
            "character_count": 42,
            "turns_count": 1,
            "warnings": [],
        }

        resp = client.post("/api/fetch-chat-link", json={"url": "https://claude.ai/share/123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "Claude"
        assert data["extracted_text"] == "Claude generated candidate evaluation notes."


def test_api_fetch_chat_link_non_http_error():
    resp = client.post("/api/fetch-chat-link", json={"url": "not-a-url"})
    assert resp.status_code == 422
    assert "Invalid URL format" in resp.json()["detail"]


def test_api_fetch_ai_link_endpoint():
    with patch("app.main.extract_chat_link", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = {
            "platform": "ChatGPT",
            "url": "https://chatgpt.com/share/abc",
            "extracted_text": "Universal AI chat transcript text.",
            "word_count": 5,
            "character_count": 35,
            "turns_count": 1,
            "warnings": [],
        }

        resp = client.post("/api/fetch-ai-link", json={"url": "https://chatgpt.com/share/abc"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "ChatGPT"
        assert data["extracted_text"] == "Universal AI chat transcript text."


def test_antibot_filter_rejections():
    # Reject short payloads (< 40 characters)
    assert is_antibot_or_junk("Short string") is True
    assert is_antibot_or_junk("") is True
    assert is_antibot_or_junk(None) is True

    # Reject Cloudflare / anti-bot challenges
    cf_sample = "Just a moment... Enable JavaScript and cookies to continue. Cloudflare Ray ID: 8f293b1."
    assert is_antibot_or_junk(cf_sample) is True

    captcha_sample = "Attention Required! | Cloudflare. Verify you are human before proceeding to access the site."
    assert is_antibot_or_junk(captcha_sample) is True

    # Valid conversation text should pass
    valid_text = (
        "Candidate demonstrates exceptional React architecture skills and deep knowledge of asynchronous state management."
    )
    assert is_antibot_or_junk(valid_text) is False


def test_clean_extracted_text_markdown_boilerplate():
    raw_jina = """Title: Candidate Performance Review - Claude Shared Chat
URL Source: https://claude.ai/share/12345
Published Time: 2026-10-10

Markdown Content:
[Skip to content]

Here is the comprehensive evaluation of John Doe's software development abilities.
He excels in Python distributed backend engineering and database optimization.

[Terms & Privacy Policy]
[Back to top]
"""
    cleaned = clean_extracted_text(raw_jina)
    assert "Title:" not in cleaned
    assert "URL Source:" not in cleaned
    assert "Markdown Content:" not in cleaned
    assert "[Skip to content]" not in cleaned
    assert "[Back to top]" not in cleaned
    assert "comprehensive evaluation of John Doe" in cleaned
    assert "distributed backend engineering" in cleaned


@pytest.mark.anyio
async def test_multi_tier_cascade_jina_first():
    with patch("app.services.chat_link_extractor.attempt_jina_reader", new_callable=AsyncMock) as mock_jina:
        mock_jina.return_value = "Candidate demonstrated exceptional performance during the system design rounds."

        res = await extract_chat_link("https://chatgpt.com/share/abc-123")
        assert res["platform"] == "ChatGPT"
        assert "Candidate demonstrated exceptional" in res["extracted_text"]
        assert mock_jina.called


@pytest.mark.anyio
async def test_multi_tier_cascade_scraper_api_fallback(monkeypatch):
    monkeypatch.setenv("SCRAPER_API_KEY", "test-key-123")
    with patch("app.services.chat_link_extractor.attempt_jina_reader", new_callable=AsyncMock) as mock_jina, \
         patch("app.services.chat_link_extractor.attempt_scraper_api", new_callable=AsyncMock) as mock_scraper:
        # Jina returns None (blocked or failed)
        mock_jina.return_value = None
        mock_scraper.return_value = "ScraperAPI successfully bypassed residential anti-bot challenges with valid text."

        res = await extract_chat_link("https://gemini.google.com/share/xyz-999")
        assert res["platform"] == "Gemini"
        assert "bypassed residential anti-bot" in res["extracted_text"]
        assert mock_scraper.called


@pytest.mark.anyio
async def test_multi_tier_cascade_direct_ssr_fallback():
    with patch("app.services.chat_link_extractor.attempt_jina_reader", new_callable=AsyncMock) as mock_jina, \
         patch("app.services.chat_link_extractor.attempt_direct_ssr", new_callable=AsyncMock) as mock_ssr:
        # Jina fails, ScraperAPI has no key configured
        mock_jina.return_value = None
        mock_ssr.return_value = "Direct SSR fallback parsed server-rendered conversation text successfully."

        res = await extract_chat_link("https://claude.ai/share/claude-456")
        assert res["platform"] == "Claude"
        assert "Direct SSR fallback parsed" in res["extracted_text"]
        assert mock_ssr.called


@pytest.mark.anyio
async def test_all_tiers_blocked_raises_clear_guidance():
    with patch("app.services.chat_link_extractor.attempt_jina_reader", new_callable=AsyncMock) as mock_jina, \
         patch("app.services.chat_link_extractor.attempt_direct_ssr", new_callable=AsyncMock) as mock_ssr:
        mock_jina.return_value = None
        mock_ssr.return_value = None

        with pytest.raises(ValueError, match="Paste from Clipboard"):
            await extract_chat_link("https://chatgpt.com/share/blocked-chat")

