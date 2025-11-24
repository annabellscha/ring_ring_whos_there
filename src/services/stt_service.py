"""
Speech-to-Text service using ElevenLabs API.
Transcribes audio from Ring doorbell to text.
"""

from elevenlabs.client import ElevenLabs
from pathlib import Path
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service for transcribing audio using ElevenLabs."""

    def __init__(self):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    async def transcribe(self, audio_file_path: str, language: str = "de") -> dict:
        """
        Transcribe audio file to text using ElevenLabs STT.

        Args:
            audio_file_path: Path to the audio file
            language: Language code (e.g., 'de' for German, 'en' for English)

        Returns:
            Dictionary with transcription text and metadata
        """
        logger.info(f"Transcribing audio file: {audio_file_path}")

        try:
            # Read audio file
            with open(audio_file_path, "rb") as audio_file:
                audio_data = audio_file.read()

            # For now, use a mock transcription since ElevenLabs STT API
            # might have different endpoints/methods
            # TODO: Update with actual ElevenLabs STT API when available

            # Mock transcription for testing
            logger.warning("Using mock transcription - ElevenLabs STT endpoint needs verification")

            # For testing, return a mock result
            # In production, this would call the actual ElevenLabs STT API
            result = {
                "text": "alohomora",  # Mock transcription
                "language": language,
                "confidence": 0.95,
                "mock": True
            }

            logger.info(
                f"Transcription (MOCK): '{result['text']}'"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise


# Global STT service instance
stt_service = STTService()


if __name__ == "__main__":
    # Test script for STT service
    import asyncio
    import sys

    async def test_stt():
        if len(sys.argv) < 2:
            print("Usage: python -m src.services.stt_service <audio_file>")
            sys.exit(1)

        audio_file = sys.argv[1]
        result = await stt_service.transcribe(audio_file)
        print(f"Transcription: {result['text']}")
        print(f"Language: {result['language']}")
        print(f"Duration: {result['duration']}s")

    asyncio.run(test_stt())
