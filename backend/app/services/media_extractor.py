import os
import re
import tempfile
import base64
import subprocess
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from app.services.ai_client import get_ai_client

MAX_MEDIA_BYTES = 25 * 1024 * 1024  # 25 MB
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
SUPPORTED_MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

def is_video_file(filename: str) -> bool:
    ext = os.path.splitext(filename or "")[1].lower()
    return ext in VIDEO_EXTENSIONS

def is_audio_file(filename: str) -> bool:
    ext = os.path.splitext(filename or "")[1].lower()
    return ext in AUDIO_EXTENSIONS

def parse_youtube_video_id(url: str) -> Optional[str]:
    """Parse standard, mobile, shortened, embed, and shorts YouTube URLs."""
    if not url:
        return None
    url = url.strip()
    
    # 1. youtu.be/VIDEO_ID
    short_match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
    if short_match:
        return short_match.group(1)
        
    # 2. youtube.com/watch?v=VIDEO_ID or m.youtube.com/watch?v=VIDEO_ID
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc:
        query_params = parse_qs(parsed.query)
        if "v" in query_params and query_params["v"]:
            return query_params["v"][0]
        # /embed/VIDEO_ID, /shorts/VIDEO_ID, /v/VIDEO_ID
        path_match = re.search(r"/(?:embed|shorts|v)/([a-zA-Z0-9_-]{11})", parsed.path)
        if path_match:
            return path_match.group(1)
            
    # 3. Direct 11-character video ID
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url):
        return url

    return None

def extract_audio_from_video(video_path: str, output_audio_path: str) -> bool:
    """Extract audio track from video file using ffmpeg. Returns True if successful."""
    try:
        res = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1", output_audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return res.returncode == 0 and os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0
    except Exception:
        return False

def transcribe_file_with_ai(
    file_path: str,
    original_filename: str = "audio.mp3",
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Transcribe an audio or video file using OpenAI Whisper (whisper-1) or Gemini Multimodal API.
    """
    env_openai_key = os.getenv("OPENAI_API_KEY")
    env_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_custom_key = api_key is not None

    # Try OpenAI Whisper first if OpenAI key is present
    if (use_custom_key and provider == "openai") or (not use_custom_key and env_openai_key and provider != "gemini"):
        try:
            client, _ = get_ai_client(custom_api_key=api_key, custom_provider="openai", custom_model="gpt-4o-mini")
            with open(file_path, "rb") as audio_file:
                transcript_obj = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                text = getattr(transcript_obj, "text", "") or str(transcript_obj)
                if text.strip():
                    return text.strip()
        except Exception as e:
            # If OpenAI Whisper fails (quota or timeout), fall through to Gemini or fallback
            pass

    # Try Gemini via OpenAI compatibility interface or multimodal input
    if (use_custom_key and provider == "gemini") or env_gemini_key:
        try:
            client, gemini_model = get_ai_client(custom_api_key=api_key, custom_provider="gemini", custom_model=model)
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            b64_audio = base64.b64encode(raw_bytes).decode("utf-8")
            
            # Determine format
            ext = os.path.splitext(file_path)[1].lower().replace(".", "")
            fmt = "mp3" if ext in ("mp3", "m4a", "aac") else ("wav" if ext == "wav" else "mp3")

            response = client.chat.completions.create(
                model=gemini_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please transcribe the spoken audio verbatim with natural punctuation. Return ONLY the transcribed text without introductory or concluding remarks."},
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": b64_audio,
                                    "format": fmt
                                }
                            }
                        ]
                    }
                ]
            )
            content = response.choices[0].message.content or ""
            if content.strip():
                return content.strip()
        except Exception:
            pass

    # If both real APIs failed or quota exceeded, return a descriptive transcribed preview
    raise RuntimeError(
        "Could not transcribe media file. Please check that OPENAI_API_KEY or GEMINI_API_KEY is configured with available quota."
    )

def extract_media_file(
    filename: str,
    file_bytes: bytes,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> dict:
    """
    Extract text transcription from local Audio or Video file.
    Enforces 25MB limit.
    """
    if not file_bytes:
        raise ValueError("The uploaded media file is empty.")
    if len(file_bytes) > MAX_MEDIA_BYTES:
        raise ValueError("The media file exceeds the 25 MB upload limit.")

    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in SUPPORTED_MEDIA_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_MEDIA_EXTENSIONS))}."
        )

    is_video = is_video_file(filename)
    media_type = "video" if is_video else "audio"
    warnings = []

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file_path = os.path.join(tmpdir, f"input_media{ext}")
        with open(input_file_path, "wb") as f:
            f.write(file_bytes)

        target_transcription_path = input_file_path
        if is_video:
            extracted_audio_path = os.path.join(tmpdir, "extracted_audio.mp3")
            ffmpeg_ok = extract_audio_from_video(input_file_path, extracted_audio_path)
            if ffmpeg_ok:
                target_transcription_path = extracted_audio_path
            else:
                warnings.append("Video audio extraction via ffmpeg bypassed; submitting video stream directly.")

        try:
            transcript_text = transcribe_file_with_ai(
                target_transcription_path,
                original_filename=filename,
                api_key=api_key,
                provider=provider,
                model=model
            )
        except Exception as e:
            raise ValueError(f"Transcription failed: {str(e)}")

    transcript_text = transcript_text.strip()
    if not transcript_text:
        raise ValueError("No audible speech or transcript could be extracted from this media file.")

    return {
        "filename": filename,
        "media_type": media_type,
        "extracted_text": transcript_text,
        "word_count": len(transcript_text.split()),
        "character_count": len(transcript_text),
        "warnings": warnings
    }

def fetch_youtube_captions_or_fallback(
    url: str,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> Tuple[str, str, list[str]]:
    """
    Extracts transcript from YouTube URL:
    1. Attempts to fetch official or auto-generated captions via youtube-transcript-api.
    2. Fallback: Downloads audio stream via yt-dlp and transcribes using the AI transcription engine.
    """
    video_id = parse_youtube_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video link.")

    warnings = []
    
    # 1. Attempt to fetch captions via youtube-transcript-api
    try:
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id)
            raw = fetched.to_raw_data()
            text = " ".join(item.get("text", "") for item in raw if item.get("text"))
            if text.strip():
                return video_id, text.strip(), warnings
        except Exception:
            transcript_list = api.list(video_id)
            transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            raw = transcript.fetch().to_raw_data()
            text = " ".join(item.get("text", "") for item in raw if item.get("text"))
            if text.strip():
                return video_id, text.strip(), warnings
    except Exception as e:
        warnings.append("Official captions unavailable. Falling back to audio stream extraction via yt-dlp.")

    # 2. Fallback: Download audio stream via yt-dlp and transcribe
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_out = os.path.join(tmpdir, f"{video_id}.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_out,
            "max_filesize": MAX_MEDIA_BYTES,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        except Exception as e:
            raise ValueError(f"Could not retrieve YouTube audio stream: {str(e)}")

        downloaded_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if not f.endswith(".part")]
        if not downloaded_files:
            raise ValueError("Failed to retrieve audio stream from YouTube video.")

        audio_file_path = downloaded_files[0]
        try:
            transcript_text = transcribe_file_with_ai(
                audio_file_path,
                original_filename=f"{video_id}.mp3",
                api_key=api_key,
                provider=provider,
                model=model
            )
        except Exception as e:
            raise ValueError(f"Audio transcription for YouTube failed: {str(e)}")

    if not transcript_text.strip():
        raise ValueError("No speech or text could be extracted from this YouTube video.")

    return video_id, transcript_text.strip(), warnings

def extract_youtube(
    url: str,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> dict:
    video_id, text, warnings = fetch_youtube_captions_or_fallback(url, api_key=api_key, provider=provider, model=model)
    return {
        "filename": f"youtube_{video_id}",
        "media_type": "youtube",
        "extracted_text": text,
        "word_count": len(text.split()),
        "character_count": len(text),
        "warnings": warnings
    }
