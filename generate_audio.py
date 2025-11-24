"""
Script to generate all witch voice audio files using ElevenLabs.
"""

import asyncio
from pathlib import Path
from src.services.tts_service import tts_service


async def generate_all_audio():
    """Generate all required witch voice audio files."""

    # Define all phrases to generate
    phrases = {
        "witch_password": "Passwort?",
        "witch_welcome": "Willkommen! Drücke die Klingeltaste nochmal für 3 Sekunden zum Öffnen.",
        "witch_wrong_password": "Falsches Passwort. Versuch es nochmal!",
        "witch_access_denied": "Zugang verweigert!",
        "witch_no_audio": "Ich habe dich nicht verstanden. Bitte wiederhole!",
        "witch_error": "System-Fehler. Bitte normal klingeln.",
    }

    print("🧙‍♀️ Generating witch voice audio files with ElevenLabs...\n")

    audio_dir = Path("audio_assets")
    audio_dir.mkdir(exist_ok=True)

    for filename, text in phrases.items():
        output_path = audio_dir / f"{filename}.mp3"

        print(f"📝 Generating: {filename}")
        print(f"   Text: {text}")

        try:
            result = await tts_service.generate_audio(
                text=text,
                output_path=str(output_path)
            )
            print(f"   ✅ Saved to: {result}\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            continue

    print("🎉 All audio files generated!")
    print(f"\nGenerated files in {audio_dir}:")
    for file in sorted(audio_dir.glob("*.mp3")):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    asyncio.run(generate_all_audio())
