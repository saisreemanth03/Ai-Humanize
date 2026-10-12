import os
import re
import json
import asyncio
import shutil
import subprocess
import logging
from typing import Optional, List, Dict, Any
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


def find_system_browser() -> Optional[str]:
    """Locates an installed Chrome or Edge executable on the host machine."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


async def render_with_headless_browser(url: str, timeout_sec: float = 8.0) -> Optional[str]:
    """Runs system headless Chrome/Edge to execute client-side JavaScript (SPAs like Gemini)."""
    browser_exe = find_system_browser()
    if not browser_exe:
        return None

    def _run():
        cmd = [
            browser_exe,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--virtual-time-budget=6000",
            "--dump-dom",
            url,
        ]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=timeout_sec,
            )
            return res.stdout if res.returncode == 0 else None
        except Exception as e:
            logger.debug(f"Headless browser render failed: {e}")
            return None

    try:
        return await asyncio.to_thread(_run)
    except Exception:
        return None


def validate_any_http_url(url: str) -> str:
    """
    Universal URL validator: accepts any valid HTTP/HTTPS URL.
    Returns detected platform or domain name.
    """
    if not url or not isinstance(url, str):
        raise ValueError("Please provide a valid URL string.")

    cleaned = url.strip()
    parsed = urlparse(cleaned)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Invalid URL format. Please enter a valid web link starting with http:// or https://")

    domain = parsed.netloc.lower()
    if "chatgpt.com" in domain or "openai.com" in domain:
        return "ChatGPT"
    if "gemini.google.com" in domain or "share.gemini.google" in domain or "g.co" in domain:
        if "/app/" in parsed.path:
            raise ValueError(
                "This is a private Gemini chat URL (/app/...). "
                "Private chats cannot be fetched without being logged in. "
                "To create a public share link in Gemini: click the Share icon -> 'Share' -> 'Create public link', "
                "or click 'Manual Paste' to paste the conversation directly."
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

    # Default to formatted domain name (e.g., example.com)
    return domain.replace("www.", "")


def extract_bulk_inner_text(html_content: str) -> str:
    """
    Universal bulk visible text extraction (innerText equivalent).
    Handles modern SSR frameworks (React Router / Remix streaming payloads,
    Next.js __NEXT_DATA__, JSON-LD) and generic DOM visible text.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Fast-path for Gemini conversational elements if rendered in DOM
    gemini_bubbles = []
    for tag in soup.find_all(lambda t: (
        t.name in ("model-response", "user-query", "message-content")
        or any(c in ("model-response", "user-query", "message-content", "query-text", "response-content") for c in t.get("class", []))
    )):
        txt = tag.get_text(separator="\n", strip=True)
        if txt and txt not in gemini_bubbles:
            gemini_bubbles.append(txt)
    if gemini_bubbles:
        return "\n\n---\n\n".join(gemini_bubbles)

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
                            return "\n\n---\n\n".join(unique_responses)
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
                    return "\n\n---\n\n".join(responses)
        except Exception:
            pass

    # Universal DOM strip of non-visible / script / style elements
    for el in soup.find_all(["script", "style", "noscript", "svg", "header", "footer", "nav", "meta", "link", "bard-sidenav", "chat-notifications"]):
        el.decompose()

    # Extract all text using line break separator
    target = soup.body if soup.body else soup
    text = target.get_text(separator="\n", strip=True)

    # Normalize excessive newlines
    cleaned_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed:
            cleaned_lines.append(trimmed)

    # Filter out empty Google Gemini SPA / sign-in boilerplate
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
    meaningful_lines = [l for l in cleaned_lines if l.lower() not in gemini_shell_phrases]
    if len(meaningful_lines) < 2 and any(l.lower() in gemini_shell_phrases for l in cleaned_lines):
        # The entire content is just Google's unauthenticated login or error shell
        return ""

    raw_result = "\n\n".join(meaningful_lines) if meaningful_lines else "\n\n".join(cleaned_lines)
    if len(raw_result.split()) >= 3:
        return raw_result

    # Fallback to OpenGraph / Meta Description if visible body text is minimal
    og_desc = (
        soup.find("meta", property="og:description")
        or soup.find("meta", attrs={"name": "description"})
    )
    if og_desc and og_desc.get("content"):
        content = og_desc["content"].strip()
        if len(content.split()) >= 3 and "created with gemini" not in content.lower():
            return content

    return raw_result


async def extract_chat_link(url: str) -> Dict[str, Any]:
    """
    Universal, unrestricted background text extractor.
    Accepts any HTTP/HTTPS URL and extracts all visible text payload.
    """
    platform = validate_any_http_url(url)
    cleaned_url = url.strip()

    try:
        async with httpx.AsyncClient(
            headers=BROWSER_HEADERS,
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            response = await client.get(cleaned_url)

    except httpx.TimeoutException:
        raise ValueError(
            f"The request timed out while connecting to {platform}. "
            "Please copy and paste the chat text directly into the editor."
        )
    except httpx.RequestError as exc:
        raise ValueError(
            f"Could not connect to {platform}: {str(exc)}. "
            "Please check the URL or copy and paste the text manually."
        )

    # Check status codes
    if response.status_code == 404:
        raise ValueError(
            f"This link was not found on {platform} (HTTP 404). "
            "The page may have been deleted, expired, or entered incorrectly. "
            "Please copy and paste the text manually."
        )
    if response.status_code in (401, 403):
        raise ValueError(
            f"Access to this page on {platform} is restricted or private (HTTP {response.status_code}). "
            "Please copy and paste the text manually."
        )
    if response.status_code >= 400:
        raise ValueError(
            f"{platform} returned HTTP {response.status_code}. "
            "Please copy and paste the text manually."
        )

    # Check for ChatGPT share_not_found redirect
    if "share_not_found" in str(response.url):
        raise ValueError(
            f"This shared {platform} link was not found or has expired. "
            "The conversation may have been deleted or unshared. "
            "Please copy and paste the chat response directly into the editor."
        )

    html_content = response.text

    # Extract universal bulk visible text
    extracted_text = extract_bulk_inner_text(html_content)

    # If static extraction yielded nothing (common for client-rendered SPAs like Gemini),
    # attempt dynamic hydration via system headless browser
    if (not extracted_text or platform == "Gemini") and len(extracted_text.split()) < 10:
        rendered_html = await render_with_headless_browser(cleaned_url)
        if rendered_html:
            # Check specifically for Gemini "Link doesn't exist" or expired link
            if "link doesn't exist" in rendered_html.lower() or "deleted or not entered correctly" in rendered_html.lower():
                raise ValueError(
                    f"This {platform} share link does not exist or has expired on Google's servers. "
                    "The shared conversation may have been deleted, unshared, or entered incorrectly. "
                    "Please copy the chat text and use 'Manual Paste'."
                )
            hydrated_text = extract_bulk_inner_text(rendered_html)
            if hydrated_text and len(hydrated_text.split()) >= 3:
                extracted_text = hydrated_text

    if not extracted_text or len(extracted_text.split()) < 3:
        if platform == "Gemini":
            raise ValueError(
                "Could not extract conversation from this Gemini link. "
                "Google Gemini share links often require logging in, or the link may be private/expired. "
                "Please open the chat in Gemini, copy the text, and use 'Manual Paste'."
            )
        raise ValueError(
            f"No visible text could be extracted from {platform}. "
            "The page may require authentication, JavaScript rendering, or is empty. "
            "Please copy and paste the text directly into the editor."
        )

    warnings = []
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
