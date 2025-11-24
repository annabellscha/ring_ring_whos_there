"""
Quick test script to generate a sample audio with ElevenLabs.
Tests with a known voice ID.
"""

import asyncio
from pathlib import Path
from elevenlabs.client import ElevenLabs
from src.config import settings


async def test_voice(voice_id: str = None, text: str = "Passwort?"):
    """Test audio generation with a specific voice."""

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    # If no voice_id provided, try a common one
    if not voice_id:
        voice_id = settings.elevenlabs_voice_id

    print(f"🧙‍♀️ Testing voice generation...")
    print(f"   Voice ID: {voice_id}")
    print(f"   Text: {text}\n")

    try:
        # Generate audio
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
        )

        # Save to file
        output_path = Path("audio_assets/test_voice.mp3")
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)

        file_size = output_path.stat().st_size / 1024
        print(f"✅ Success! Audio generated:")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size:.1f} KB")
        print(f"\n🎧 Play with: open {output_path}")

        return str(output_path)

    except Exception as e:
        print(f"❌ Error: {e}\n")

        # Extract useful error info
        if "voice_not_found" in str(e):
            print("💡 The voice ID doesn't exist.")
            print("   Get a valid voice ID from: https://elevenlabs.io/app/voice-lab")
        elif "401" in str(e):
            print("💡 API key issue - check your ELEVENLABS_API_KEY")

        return None


if __name__ == "__main__":
    asyncio.run(test_voice())
