"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PasswordCheckRequest(BaseModel):
    """Request model for password checking."""

    text: str = Field(..., description="Spoken text to check against passwords")


class PasswordCheckResponse(BaseModel):
    """Response model for password checking."""

    match: bool = Field(..., description="Whether a password match was found")
    score: float = Field(..., description="Similarity score (0-100)")
    matched_password: Optional[str] = Field(None, description="The matched password")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DoorbellEvent(BaseModel):
    """Model for doorbell event from Ring."""

    event_type: str = Field(..., description="Type of event (e.g., 'doorbell_pressed')")
    device_id: str = Field(..., description="Ring device ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    video_url: Optional[str] = Field(None, description="URL to video stream")
    audio_stream_url: Optional[str] = Field(None, description="URL to audio stream")


class DoorbellFlowResult(BaseModel):
    """Result of the complete doorbell flow."""

    status: str = Field(
        ..., description="Flow status (success, denied, error, timeout)"
    )
    score: Optional[float] = Field(None, description="Password match score")
    attempts: int = Field(..., description="Number of attempts made")
    transcription: Optional[str] = Field(None, description="Transcribed text")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: float = Field(..., description="Total flow duration in milliseconds")
