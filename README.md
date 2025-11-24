# Ring Ring Who's There

A magical door opening system with witch voice authentication that integrates with Amazon Ring doorbell.

## Overview

When someone rings the doorbell, the system responds with a witch voice asking "Passwort?" (Password?). The visitor's spoken response is transcribed using speech-to-text, matched against configured passwords using fuzzy matching, and grants access if the password is correct.

## Features

- 🧙‍♀️ Witch voice text-to-speech (ElevenLabs)
- 🎤 Speech-to-text transcription (OpenAI Whisper)
- 🔍 Fuzzy password matching (handles typos and pronunciation variations)
- 📊 Full tracing and monitoring (Langfuse)
- 🚪 Amazon Ring doorbell integration
- 🔒 Secure password validation with retry logic

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **ElevenLabs**: For text-to-speech (witch voice)
- **OpenAI**: For Whisper speech-to-text
- **Langfuse**: For tracing and monitoring
- **Ring**: Your Ring account credentials

### 3. Run the Application

```bash
# Development mode with auto-reload
python src/main.py

# Or with uvicorn directly
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Testing Individual Services

### Test TTS Service
```bash
python -m src.services.tts_service "Passwort?"
```

### Test STT Service
```bash
python -m src.services.stt_service path/to/audio.mp3
```

### Test Password Matching
```bash
python -m src.services.password_service
```

### Test Tracing
```bash
python -m src.services.tracing_service
```

## Development Status

✅ Project setup and structure
✅ Configuration management
✅ Text-to-speech service
✅ Speech-to-text service
✅ Password matching with fuzzy logic
✅ Tracing and monitoring setup
⏳ Ring API integration (in progress)
⏳ Doorbell workflow orchestration
⏳ Webhook endpoints

## Ring API Integration

⚠️ **Note**: Ring does not have an official public API. Integration options are being researched.

See `SPECS.md` and `PLAN.md` for detailed documentation.