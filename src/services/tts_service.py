"""
Text-to-Speech service using ElevenLabs API.
Generates witch voice audio for doorbell responses.
"""

from elevenlabs.client import ElevenLabs
from pathlib import Path
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service for generating witch voice audio."""

    def __init__(self, voice_id: str = None):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_id = voice_id or settings.elevenlabs_voice_id

    async def generate_audio(self, text: str, output_path: str) -> str:
        """
        Generate audio from text using ElevenLabs.

        Args:
            text: The text to convert to speech
            output_path: Path where the audio file should be saved

        Returns:
            Path to the generated audio file
        """
        logger.info(f"Generating audio for text: {text}")

        try:
            # Generate audio using ElevenLabs client
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
            )

            # Save audio to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write audio chunks to file
            with open(output_file, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)

            logger.info(f"Audio saved to: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            raise


# Global TTS service instance
tts_service = TTSService()


if __name__ == "__main__":
    # Test script for TTS service
    import asyncio
    import sys

    async def test_tts():
        if len(sys.argv) > 1:
            text = sys.argv[1]
        else:
            text = "Passwort?"

        output = f"audio_assets/test_{text.replace(' ', '_')}.mp3"
        await tts_service.generate_audio(text, output)
        print(f"Generated audio: {output}")

    asyncio.run(test_tts())
