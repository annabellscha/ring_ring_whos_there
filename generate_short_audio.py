"""
Generate essential witch voice audio files with shorter phrases.
Optimized for limited credits.
"""

import asyncio
from pathlib import Path
from elevenlabs.client import ElevenLabs
from src.config import settings


async def generate_audio_files():
    """Generate shortened audio files for the witch voice system."""

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

    # Shortened phrases to save credits
    phrases = {
        "witch_password": "Passwort?",
        "witch_welcome": "Willkommen!",
        "witch_wrong": "Falsch!",
        "witch_denied": "Verweigert!",
        "witch_repeat": "Wiederholen!",
    }

    print("🧙‍♀️ Generating witch voice audio files...\n")

    audio_dir = Path("audio_assets")
    audio_dir.mkdir(exist_ok=True)

    success_count = 0
    failed_count = 0

    for filename, text in phrases.items():
        output_path = audio_dir / f"{filename}.mp3"

        print(f"📝 {filename}: '{text}'")

        try:
            # Generate audio
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
            )

            # Save to file
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)

            file_size = output_path.stat().st_size / 1024
            print(f"   ✅ Success! ({file_size:.1f} KB)\n")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            failed_count += 1

            # If quota exceeded, stop trying
            if "quota_exceeded" in str(e):
                print("⚠️  Credit limit reached. Stopping generation.")
                print("   Add more credits to continue.\n")
                break

    print(f"📊 Summary:")
    print(f"   ✅ Generated: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"\n🎧 Play audio with: open audio_assets/witch_password.mp3")


if __name__ == "__main__":
    asyncio.run(generate_audio_files())
