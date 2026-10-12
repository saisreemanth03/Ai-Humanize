from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

Context = Literal[
    "Recruiter Feedback & Rejection Emails",
    "Candidate Communication & Offer Letters",
    "Adaptive Interview Question Refinement",
    "Candidate Evaluation Summaries & Reports",
    "General Professional Writing",
    "Audio / Video Transcript & Spoken Dialogue",
    "Spoken Dialogue & Transcripts",
    "General Writing",
    "Professional Communication",
    "Academic Writing",
    "Reports and Summaries",
    "Interview Questions",
    "Candidate Communication",
    "Business Documents"
]

Tone = Literal["Natural", "Professional", "Conversational", "Polished", "Concise"]

class HumanizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    context: Context = "General Professional Writing"
    tone: Tone = "Natural"
    minimal_rewrite: bool = False
    api_key: Optional[str] = None
    provider: Optional[Literal["gemini", "openai"]] = None
    model: Optional[str] = None

class RoboticAnalysis(BaseModel):
    detected_cliches: list[str] = []
    cliche_count: int = 0
    robotic_score: str = "Low"
    sentence_variance: float = 0.0
    sentence_count: int = 0
    description: str = ""
    eliminated_cliches: list[str] = []

class EntityGuardrailResult(BaseModel):
    all_entities: list[str] = []
    entities_preserved: list[str] = []
    missing_entities: list[str] = []
    preservation_rate: float = 100.0
    is_100_percent_preserved: bool = True
    extracted_categories: dict[str, Any] = {}

class HumanizeResponse(BaseModel):
    humanized_text: str
    changes_summary: str
    extracted_entities: dict[str, Any]
    meaning_validation: dict[str, Any]
    factuality_validation: dict[str, Any]
    warnings: list[str]
    # Enhanced attributes for Problem Track 02 verification pipeline
    meaning_preserved: bool = True
    entities_preserved: list[str] = []
    unsupported_claims_detected: bool = False
    factuality_confidence: int = 100
    preserved_terms: list[str] = []
    semantic_similarity_score: int = 100
    robotic_analysis: Optional[RoboticAnalysis] = None
    entity_guardrail: Optional[EntityGuardrailResult] = None

class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)

class YouTubeExtractRequest(BaseModel):
    url: str = Field(min_length=1)

class MediaExtractResponse(BaseModel):
    filename: str
    media_type: str
    extracted_text: str
    word_count: int
    character_count: int
    warnings: list[str] = []

class ChatLinkExtractRequest(BaseModel):
    url: str = Field(min_length=1)

class ChatLinkExtractResponse(BaseModel):
    platform: str
    url: str
    extracted_text: str
    word_count: int
    character_count: int
    turns_count: int = 1
    warnings: list[str] = []

