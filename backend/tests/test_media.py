import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services import media_extractor

client = TestClient(app)

def test_extract_local_video_success(monkeypatch):
    """Verify local video upload extraction with mocked transcriber."""
    monkeypatch.setattr(
        media_extractor,
        "transcribe_file_with_ai",
        lambda file_path, original_filename="video.mp4", **kwargs: "Candidate John is proficient in React and Python."
    )
    # Mock extract_audio_from_video to return True
    monkeypatch.setattr(
        media_extractor,
        "extract_audio_from_video",
        lambda video_path, output_audio: True
    )

    fake_video_bytes = b"\x00\x00\x00 ftypisom" + (b"mock_video_data" * 10)
    response = client.post(
        "/api/extract-media",
        files={"file": ("interview.mp4", fake_video_bytes, "video/mp4")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "interview.mp4"
    assert data["media_type"] == "video"
    assert "React" in data["extracted_text"]
    assert data["word_count"] > 0

def test_extract_local_audio_success(monkeypatch):
    """Verify local audio upload extraction with mocked transcriber."""
    monkeypatch.setattr(
        media_extractor,
        "transcribe_file_with_ai",
        lambda file_path, original_filename="audio.mp3", **kwargs: "Sarah Connor completed the technical assessment on Oct 11."
    )

    fake_audio_bytes = b"ID3\x03\x00\x00" + (b"mock_audio_data" * 10)
    response = client.post(
        "/api/extract-media",
        files={"file": ("recording.mp3", fake_audio_bytes, "audio/mpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "recording.mp3"
    assert data["media_type"] == "audio"
    assert "Sarah Connor" in data["extracted_text"]
    assert data["word_count"] > 0

def test_extract_youtube_success(monkeypatch):
    """Verify YouTube caption fetch extraction with mock."""
    sample_text = "Welcome to the system design interview. Today we will delve into building a cache."
    monkeypatch.setattr(
        media_extractor,
        "fetch_youtube_captions_or_fallback",
        lambda url, **kwargs: ("dQw4w9WgXcQ", sample_text, [])
    )

    response = client.post(
        "/api/extract-youtube",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["media_type"] == "youtube"
    assert data["extracted_text"] == sample_text
    assert data["word_count"] > 0

def test_extract_media_file_size_limit():
    """Verify HTTP 413 for media files exceeding 25MB limit."""
    oversized_bytes = b"0" * (25 * 1024 * 1024 + 10)
    response = client.post(
        "/api/extract-media",
        files={"file": ("large_video.mp4", oversized_bytes, "video/mp4")}
    )
    assert response.status_code == 413
    assert "25 MB" in response.json()["detail"]

def test_extract_media_unsupported_format():
    """Verify HTTP 422 for unsupported media formats."""
    response = client.post(
        "/api/extract-media",
        files={"file": ("document.pdf", b"fake_pdf_data", "application/pdf")}
    )
    assert response.status_code == 422
    assert "Unsupported file format" in response.json()["detail"]

def test_extract_media_empty_file():
    """Verify HTTP 422 for empty file uploads."""
    response = client.post(
        "/api/extract-media",
        files={"file": ("empty.mp3", b"", "audio/mpeg")}
    )
    assert response.status_code == 422
    assert "empty" in response.json()["detail"]

def test_extract_youtube_invalid_url():
    """Verify HTTP 422 for invalid YouTube URLs."""
    response = client.post(
        "/api/extract-youtube",
        json={"url": "https://vimeo.com/123456"}
    )
    assert response.status_code == 422
    assert "Invalid YouTube URL" in response.json()["detail"]

def test_humanize_media_workflow(monkeypatch):
    """Verify humanize-media endpoint processes audio and humanizes it."""
    monkeypatch.setattr(
        media_extractor,
        "transcribe_file_with_ai",
        lambda *args, **kwargs: "Candidate John scored 95% on React on Oct 11. Can you delve into his performance?"
    )
    fake_audio_bytes = b"ID3\x03\x00\x00" + (b"mock_audio" * 5)
    response = client.post(
        "/api/humanize-media",
        files={"file": ("feedback.mp3", fake_audio_bytes, "audio/mpeg")},
        data={"context": "Candidate Evaluation Summaries & Reports", "tone": "Natural"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "extraction" in data
    assert "result" in data
    assert data["result"]["humanized_text"]

def test_humanize_youtube_workflow(monkeypatch):
    """Verify humanize-youtube endpoint extracts captions and humanizes them."""
    monkeypatch.setattr(
        media_extractor,
        "fetch_youtube_captions_or_fallback",
        lambda *args, **kwargs: ("abc12345678", "Sarah scored 90% on Python. Can you delve into her assessment?", [])
    )
    response = client.post(
        "/api/humanize-youtube",
        json={"url": "https://youtu.be/abc12345678"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "extraction" in data
    assert "result" in data
    assert data["result"]["humanized_text"]
