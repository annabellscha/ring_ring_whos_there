"""
Text-to-Speech service using ElevenLabs API.

This module provides functionality to generate audio files from text using
ElevenLabs' multilingual TTS API. The service is configured to use a specific
witch voice for doorbell responses, creating an immersive authentication
experience.

Example:
    ```python
    from src.services.tts_service import tts_service
    
    await tts_service.generate_audio("Passwort?", "output.mp3")
    ```

Note:
    The service uses the "eleven_multilingual_v2" model which supports
    multiple languages including German and English.
"""

from elevenlabs.client import ElevenLabs
from pathlib import Path
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service for generating witch voice audio.
    
    This service converts text strings into audio files using ElevenLabs'
    text-to-speech API. It's configured with a specific voice ID to maintain
    consistent character voice across all doorbell interactions.
    
    Attributes:
        client (ElevenLabs): The ElevenLabs API client instance.
        voice_id (str): The voice ID to use for speech generation.
    """

    def __init__(self, voice_id: str = None):
        """
        Initialize the TTS service with ElevenLabs API credentials.
        
        Args:
            voice_id: Optional voice ID to override the default from settings.
                If not provided, uses the voice ID from configuration.
        
        Raises:
            ValueError: If ElevenLabs API key is not configured.
        """
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_id = voice_id or settings.elevenlabs_voice_id

    async def generate_audio(self, text: str, output_path: str) -> str:
        """
        Generate audio from text using ElevenLabs TTS API.

        Converts the provided text into speech using the configured witch voice
        and saves it as an audio file. The output directory is created
        automatically if it doesn't exist.

        Args:
            text: The text to convert to speech. Can be in any language
                supported by the multilingual model (e.g., German, English).
            output_path: Path where the generated audio file should be saved.
                The file format is determined by the extension (typically .mp3).
                Parent directories will be created if they don't exist.

        Returns:
            The absolute path to the generated audio file as a string.

        Raises:
            ValueError: If the text is empty or output_path is invalid.
            PermissionError: If the output directory cannot be created or
                the file cannot be written.
            Exception: If the ElevenLabs API call fails.

        Example:
            ```python
            audio_path = await tts_service.generate_audio(
                "Passwort?", 
                "audio_assets/witch_password.mp3"
            )
            # audio_path: "/path/to/audio_assets/witch_password.mp3"
            ```

        Note:
            Uses the "eleven_multilingual_v2" model which supports multiple
            languages. The audio is streamed in chunks and written to disk.
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
