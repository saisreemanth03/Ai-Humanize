import os
import re
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 20000

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

ANTIBOT_SIGNATURES = [
    "just a moment...",
    "enable javascript and cookies to continue",
    "verify you are human",
    "attention required! | cloudflare",
    "checking your browser before accessing",
    "cloudflare ray id",
    "please turn javascript on and reload the page",
    "please verify that you are not a robot",
    "cf-browser-verification",
    "challenge-running",
    "access denied",
    "security check to continue",
    "recaptcha",
    "cf-turnstile",
    "ray id:",
    "ddos protection by cloudflare",
]


JUNK_SHELL_PATTERNS = [
    "log in to get answers",
    "what's on your mind today?",
    "what’s on your mind today?",
    "what's on the agenda today?",
    "what’s on the agenda today?",
    "sign up for free",
    "get responses tailored to you",
    "see plans and pricing",
    "gemini - direct access to google ai",
    "link doesn't exist",
    "the link might have been deleted",
    "conversation has been deleted",
    "can't load shared conversation",
    "can’t load shared conversation",
    "unable to load conversation",
    "conversation not found",
    "share not found",
    "stay logged out",
    "chats may be reviewed and used to improve our ai models",
    "chat history\nnew chat",
    "get started for free or download the app",
]


def is_antibot_or_junk(text: Optional[str]) -> bool:
    """
    Checks if extracted text is an anti-bot challenge page or junk content.
    Rejects payloads with fewer than 40 characters of meaningful content,
    containing known CAPTCHA/Cloudflare challenge phrases, or containing
    empty unauthenticated SPA login/landing shell boilerplate.
    """
    if not text or not isinstance(text, str):
        return True

    trimmed = text.strip()
    if len(trimmed) < 40:
        return True

    lower = trimmed.lower()
    for sig in ANTIBOT_SIGNATURES:
        if sig in lower:
            return True

    # Reject empty landing shells / login barriers returned by SPAs
    for shell in JUNK_SHELL_PATTERNS:
        if shell in lower:
            return True

    return False


def clean_extracted_text(text: Optional[str]) -> str:
    """
    Cleans out markdown boilerplate (such as Title:, URL Source:, Markdown Content:)
    and navigation footer noise, preserving the clean conversation text.
    """
    if not text or not isinstance(text, str):
        return ""

    lines = text.splitlines()
    cleaned_lines: List[str] = []
    header_mode = True

    for line in lines:
        stripped = line.strip()

        # Strip metadata boilerplate headers produced by Jina Reader
        if header_mode:
            if (
                stripped.startswith("Title:")
                or stripped.startswith("URL Source:")
                or stripped.startswith("Published Time:")
            ):
                continue
            if stripped.startswith("Markdown Content:"):
                header_mode = False
                continue
            if not stripped:
                continue
            # First non-header line ends header mode
            header_mode = False

        # Filter out common markdown navigation/shell noise
        lower_line = stripped.lower()
        if lower_line in (
            "[skip to content]",
            "[log in]",
            "[sign up]",
            "terms & privacy policy",
            "terms",
            "privacy policy",
            "terms of service",
            "[back to top]",
            "learn more",
            "stay logged out",
        ):
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    # Normalize excessive blank lines (3+ consecutive newlines to 2)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def validate_any_http_url(url: str) -> str:
    """
    Universal URL validator: accepts any valid HTTP/HTTPS URL.
    Returns detected platform or formatted domain name.
    """
    if not url or not isinstance(url, str) or not url.strip():
        raise ValueError("Please provide a valid URL string.")

    cleaned = url.strip()
    parsed = urlparse(cleaned)

    if not parsed.scheme:
        first_segment = cleaned.split("/")[0]
        if "." in first_segment and not first_segment.startswith("."):
            cleaned = "https://" + cleaned
            parsed = urlparse(cleaned)
        else:
            raise ValueError("Invalid URL format. Please enter a valid web link starting with http:// or https://")

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Invalid URL format. Please enter a valid web link starting with http:// or https://")

    domain = parsed.netloc.lower()
    if "chatgpt.com" in domain or "openai.com" in domain:
        if "/c/" in parsed.path:
            raise ValueError(
                "This is a private ChatGPT chat URL (/c/...). "
                "Private chats cannot be fetched without being logged in. "
                "To create a public share link in ChatGPT: click the Share icon -> 'Create link', "
                "or use 'Paste from Clipboard' to paste the conversation directly."
            )
        return "ChatGPT"

    if "gemini.google.com" in domain or "share.gemini.google" in domain or "g.co" in domain:
        if "/app/" in parsed.path:
            raise ValueError(
                "This is a private Gemini chat URL (/app/...). "
                "Private chats cannot be fetched without being logged in. "
                "To create a public share link in Gemini: click the Share icon -> 'Share' -> 'Create public link', "
                "or use 'Paste from Clipboard' to paste the conversation directly."
            )
        return "Gemini"

    if "claude.ai" in domain or "anthropic.com" in domain:
        return "Claude"
    if "perplexity.ai" in domain:
        return "Perplexity"
    if "deepseek.com" in domain:
        return "DeepSeek"
    if "huggingface.co" in domain:
        return "HuggingFace"

    # Default to formatted domain name (e.g. example.com)
    return domain.replace("www.", "")


def extract_bulk_inner_text(html_content: str) -> str:
    """
    Universal bulk visible text extraction (innerText equivalent).
    Handles modern SSR frameworks (React Router / Remix streaming payloads,
    Next.js __NEXT_DATA__, Gemini DOM components) and generic DOM visible text.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Fast-path for Gemini conversational elements if rendered in DOM
    gemini_bubbles = []
    for tag in soup.find_all(
        lambda t: (
            t.name in ("model-response", "user-query", "message-content")
            or any(
                c in ("model-response", "user-query", "message-content", "query-text", "response-content")
                for c in t.get("class", [])
            )
        )
    ):
        txt = tag.get_text(separator="\n", strip=True)
        if txt and txt not in gemini_bubbles:
            gemini_bubbles.append(txt)
    if gemini_bubbles:
        return clean_extracted_text("\n\n---\n\n".join(gemini_bubbles))

    # 1. Fast-path for React Router / Remix streaming SSR apps (ChatGPT's current architecture)
    for s in soup.find_all("script"):
        txt = s.string or s.text or ""
        if "__reactRouterContext" in txt and "enqueue(" in txt and len(txt) > 1000:
            try:
                idx1 = txt.find("enqueue(") + len("enqueue(")
                idx2 = txt.rfind(");")
                raw = txt[idx1:idx2].strip()
                val = json.loads(raw)
                arr = json.loads(val)
                if isinstance(arr, list):
                    def resolve_dict(d):
                        if not isinstance(d, dict):
                            return d
                        res = {}
                        for k, v in d.items():
                            k_idx = k.lstrip('_')
                            real_k = arr[int(k_idx)] if k_idx.isdigit() and int(k_idx) < len(arr) else k
                            res[real_k] = v
                        return res

                    responses = []
                    for el in arr:
                        if isinstance(el, dict):
                            rd = resolve_dict(el)
                            if "author" in rd and "content" in rd:
                                author_obj = resolve_dict(arr[rd["author"]]) if isinstance(rd["author"], int) else rd["author"]
                                role = arr[author_obj.get("role")] if isinstance(author_obj.get("role"), int) else author_obj.get("role")
                                content_obj = resolve_dict(arr[rd["content"]]) if isinstance(rd["content"], int) else rd["content"]
                                parts_idx = content_obj.get("parts")
                                parts_list = arr[parts_idx] if isinstance(parts_idx, int) else parts_idx
                                if isinstance(parts_list, list):
                                    for p in parts_list:
                                        part_text = arr[p] if isinstance(p, int) else p
                                        if isinstance(part_text, str) and part_text.strip():
                                            responses.append(part_text.strip())
                    if responses:
                        seen = set()
                        unique_responses = []
                        for r in responses:
                            if r not in seen:
                                seen.add(r)
                                unique_responses.append(r)
                        if unique_responses:
                            return clean_extracted_text("\n\n---\n\n".join(unique_responses))
            except Exception:
                pass

    # 2. Fast-path for Next.js SSR apps if conversation JSON is present
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data and next_data.string:
        try:
            data = json.loads(next_data.string)
            page_props = data.get("props", {}).get("pageProps", {})
            mapping = (
                page_props.get("serverResponse", {}).get("data", {}).get("mapping")
                or page_props.get("sharedConversation", {}).get("mapping")
                or page_props.get("mapping")
            )
            if isinstance(mapping, dict):
                responses = []
                for _, node in mapping.items():
                    if isinstance(node, dict):
                        msg = node.get("message")
                        if isinstance(msg, dict) and msg.get("author", {}).get("role") == "assistant":
                            parts = msg.get("content", {}).get("parts", [])
                            text_parts = [str(p) for p in parts if isinstance(p, (str, int, float))]
                            if text_parts:
                                responses.append("\n\n".join(text_parts).strip())
                if responses:
                    return clean_extracted_text("\n\n---\n\n".join(responses))
        except Exception:
            pass

    # Universal DOM strip of non-visible / script / style / nav / header elements
    for el in soup.find_all([
        "script", "style", "noscript", "svg", "header", "footer", "nav",
        "meta", "link", "bard-sidenav", "chat-notifications"
    ]):
        el.decompose()

    # Prefer <article> or <main> container if present for cleaner conversation content
    target_container = soup.find("article") or soup.find("main") or (soup.body if soup.body else soup)
    text = target_container.get_text(separator="\n", strip=True)

    # Normalize lines
    cleaned_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed:
            cleaned_lines.append(trimmed)

    # Filter out empty Google Gemini and ChatGPT SPA / sign-in boilerplate
    gemini_shell_phrases = {
        "gemini - direct access to google ai",
        "sign in",
        "google apps",
        "to save activity",
        "expand menu",
        "close sidebar",
        "about gemini",
        "get gemini app",
        "subscriptions",
        "for business",
        "link doesn't exist",
        "the link might have been deleted or not entered correctly.",
    }
    chatgpt_shell_phrases = {
        "skip to content",
        "what's on the agenda today?",
        "what’s on the agenda today?",
        "chatgpt is ai. by using it, you agree to our",
        "chats may be reviewed and used to improve our ai models.",
        "conversation has been deleted. start a new chat.",
        "conversation has been deleted",
        "share not found",
        "terms & privacy policy",
        "terms",
        "privacy policy",
        "learn more",
        "log in",
        "sign up",
        "stay logged out",
        "get started for free or download the app.",
    }
    meaningful_lines = [
        l for l in cleaned_lines
        if l.lower() not in gemini_shell_phrases and l.lower() not in chatgpt_shell_phrases
    ]
    if len(meaningful_lines) < 2 and any(
        (l.lower() in gemini_shell_phrases or l.lower() in chatgpt_shell_phrases) for l in cleaned_lines
    ):
        return ""

    raw_result = "\n\n".join(meaningful_lines) if meaningful_lines else "\n\n".join(cleaned_lines)
    cleaned_result = clean_extracted_text(raw_result)
    if len(cleaned_result.split()) >= 3:
        return cleaned_result

    # Fallback to OpenGraph / Meta Description if visible body text is minimal
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if og_desc and og_desc.get("content"):
        content = og_desc["content"].strip()
        if len(content.split()) >= 3 and "created with gemini" not in content.lower():
            return clean_extracted_text(content)

    return cleaned_result


async def attempt_jina_reader(target_url: str) -> Optional[str]:
    """
    Attempt 2A: Jina Browser Engine
    Requests https://r.jina.ai/{target_url} using httpx.AsyncClient with browser engine headers.
    """
    jina_endpoint = f"https://r.jina.ai/{target_url}"
    headers = {
        "X-Engine": "browser",
        "X-Return-Format": "text",
        "X-Timeout": "30",
        "Accept": "text/plain",
        "User-Agent": BROWSER_HEADERS["User-Agent"],
    }
    try:
        async with httpx.AsyncClient(headers=headers, timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(jina_endpoint)
            if resp.status_code == 200 and resp.text:
                cleaned = clean_extracted_text(resp.text)
                if not is_antibot_or_junk(cleaned):
                    return cleaned
    except Exception as e:
        logger.debug(f"Attempt 2A (Jina Browser Engine) error for {target_url}: {e}")
    return None


async def attempt_scraper_api(target_url: str, api_key: str) -> Optional[str]:
    """
    Attempt 2B: Residential Proxy API Fallback
    Routes request through ScraperAPI with render=true&premium=true and parses visible text with BeautifulSoup.
    """
    endpoint = (
        f"http://api.scraperapi.com?api_key={api_key}&url={target_url}&render=true&premium=true"
    )
    try:
        async with httpx.AsyncClient(timeout=35.0, follow_redirects=True) as client:
            resp = await client.get(endpoint)
            if resp.status_code == 200 and resp.text:
                extracted = extract_bulk_inner_text(resp.text)
                cleaned = clean_extracted_text(extracted)
                if not is_antibot_or_junk(cleaned):
                    return cleaned
    except Exception as e:
        logger.debug(f"Attempt 2B (ScraperAPI Proxy) error for {target_url}: {e}")
    return None


async def attempt_direct_ssr(target_url: str) -> Optional[str]:
    """
    Direct SSR Hydration Parse
    Fetches URL with realistic Chrome headers, extracting embedded React Router /
    __NEXT_DATA__ JSON hydration payloads or clean DOM text.
    """
    try:
        async with httpx.AsyncClient(
            headers=BROWSER_HEADERS,
            timeout=8.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(target_url)

            # Check for ChatGPT share_not_found redirect
            if "share_not_found" in str(resp.url):
                return None

            if resp.status_code == 200 and resp.text:
                lower_html = resp.text.lower()
                if (
                    "can't load shared conversation" in lower_html
                    or "can’t load shared conversation" in lower_html
                    or "conversation has been deleted" in lower_html
                    or "share not found" in lower_html
                    or "the conversation you are looking for doesn't exist" in lower_html
                ):
                    return None

                extracted = extract_bulk_inner_text(resp.text)
                cleaned = clean_extracted_text(extracted)
                if not is_antibot_or_junk(cleaned):
                    return cleaned
    except Exception as e:
        logger.debug(f"Direct SSR Parse error for {target_url}: {e}")
    return None


async def extract_chat_link(url: str) -> Dict[str, Any]:
    """
    Multi-Tier Cloud Extraction Service (FastAPI Backend Cascade):
    - Attempt 2A: Jina Browser Engine (r.jina.ai with X-Engine: browser)
    - Attempt 2B: Residential Proxy API Fallback (ScraperAPI if SCRAPER_API_KEY is configured)
    - Attempt 2C: Direct SSR Hydration Parse (Realistic Chrome headers + JSON hydration / DOM parsing)
    Validates output through Anti-Bot & Junk Content Filter before returning.
    """
    platform = validate_any_http_url(url)
    cleaned_url = url.strip()
    if not cleaned_url.startswith("http://") and not cleaned_url.startswith("https://"):
        cleaned_url = "https://" + cleaned_url

    # Intelligent Auto-Correction for Gemini short-links (e.g. l vs I typographical confusion)
    if "share.gemini.google" in cleaned_url and ("l" in cleaned_url or "I" in cleaned_url):
        try:
            parts = cleaned_url.split("/")
            slug = parts[-1]
            swapped = slug.replace("l", "I")
            alt_url = "/".join(parts[:-1]) + "/" + swapped
            with httpx.Client(timeout=3.0, follow_redirects=True) as check_client:
                r_check = check_client.get(alt_url)
                if r_check.status_code == 200:
                    cleaned_url = alt_url
        except Exception:
            pass

    extracted_text: Optional[str] = None
    extraction_tier: str = "unknown"

    # Attempt 2A: Jina Browser Engine
    extracted_text = await attempt_jina_reader(cleaned_url)
    if extracted_text and not is_antibot_or_junk(extracted_text):
        extraction_tier = "jina_browser"
    else:
        extracted_text = None

    # Attempt 2B: Residential Proxy API Fallback (if SCRAPER_API_KEY is configured)
    if not extracted_text:
        scraper_api_key = os.environ.get("SCRAPER_API_KEY", "").strip()
        if scraper_api_key:
            extracted_text = await attempt_scraper_api(cleaned_url, scraper_api_key)
            if extracted_text and not is_antibot_or_junk(extracted_text):
                extraction_tier = "scraper_api_proxy"
            else:
                extracted_text = None

    # Attempt 2C: Direct SSR Hydration Parse
    if not extracted_text:
        extracted_text = await attempt_direct_ssr(cleaned_url)
        if extracted_text and not is_antibot_or_junk(extracted_text):
            extraction_tier = "direct_ssr"
        else:
            extracted_text = None

    # If all tiers failed or were blocked
    if not extracted_text or is_antibot_or_junk(extracted_text):
        if platform == "Gemini":
            raise ValueError(
                "Could not extract conversation from this Gemini link. "
                "Google Gemini share links often require logging in or are protected by verification. "
                "Please copy the chat text and use 'Paste from Clipboard'."
            )
        if platform == "ChatGPT":
            raise ValueError(
                "Could not extract conversation from this ChatGPT link. "
                "The conversation may be private, expired, or protected by Cloudflare verification. "
                "Please copy the chat text and use 'Paste from Clipboard'."
            )
        raise ValueError(
            f"Unable to extract text from this {platform} link. "
            "The link is protected by Cloudflare anti-bot verification or requires account login. "
            "Please copy the conversation and use 'Paste from Clipboard'."
        )

    warnings: List[str] = []
    if len(extracted_text) > MAX_TEXT_CHARS:
        extracted_text = extracted_text[:MAX_TEXT_CHARS]
        warnings.append(
            f"Extracted content was limited to {MAX_TEXT_CHARS:,} characters for optimal humanization processing."
        )

    return {
        "platform": platform,
        "url": cleaned_url,
        "extracted_text": extracted_text,
        "word_count": len(extracted_text.split()),
        "character_count": len(extracted_text),
        "turns_count": 1,
        "warnings": warnings,
    }
