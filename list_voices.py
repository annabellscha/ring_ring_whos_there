"""
Script to list available voices from ElevenLabs account.
"""

from elevenlabs.client import ElevenLabs
from src.config import settings


def list_voices():
    """List all available voices in your ElevenLabs account."""

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    print("🎭 Fetching available voices from ElevenLabs...\n")

    try:
        voices = client.voices.get_all()

        print(f"Found {len(voices.voices)} voices:\n")

        for voice in voices.voices:
            print(f"📝 Name: {voice.name}")
            print(f"   ID: {voice.voice_id}")
            print(f"   Category: {voice.category}")
            if voice.labels:
                print(f"   Labels: {voice.labels}")
            print()

        print("\n💡 To use a voice, copy its ID to your .env file:")
        print("   ELEVENLABS_VOICE_ID=<voice_id>")

    except Exception as e:
        print(f"❌ Error fetching voices: {e}")


if __name__ == "__main__":
    list_voices()
