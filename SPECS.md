# Ring Ring Who's There - Specifications

## Project Overview

A magical door opening system with a witch voice that works via Amazon Ring Doorbell and uses Speech-to-Text for password authentication.

## Functional Requirements

### Core Features

#### 1. Doorbell Event Detection
- **Trigger**: Amazon Ring Doorbell detects doorbell press
- **Action**: System automatically activates and starts interaction

#### 2. Witch Response (Text-to-Speech)
- **Provider**: Open AI whisper
- **Voice**: Witch-like voice
- **Text**:  German: "Passwort?"
- **Output**: Audio plays through Ring intercom speaker

#### 3. Voice Input (Speech-to-Text)
- **Provider**: Whisper (OpenAI API) 
- **Input**: Audio recording from Ring Doorbell (5-10 seconds)
- **Output**: Transcribed text of the response

#### 4. Password Validation
- **Matching Method**: Fuzzy Matching (for pronunciation variations)
- **Libraries**:
  - Option 1: `fuzzywuzzy` / `rapidfuzz` (Levenshtein Distance)
  - Option 2: `jellyfish` (Phonetic Similarity)
- **Threshold**: ~80% similarity (configurable)
- **Password Storage**: Configuration file or Environment Variables

#### 5. Door Opening
- **Mechanism**: Instructions via Ring intercom
- **Message**: "Welcome! Press the doorbell button again for 3 seconds to open"
- **Note**: No Smart Lock integration - person uses normal intercom function

#### 6. Tracing & Monitoring
- **Provider**: Langfuse
- **To trace**:
  - Doorbell Events (Timestamp, Duration)
  - TTS Generation (Latency, Audio Length)
  - STT Transcription (Latency, Confidence Score)
  - Password Matches (Success/Failure, Similarity Score)
  - Errors and Exceptions
  - End-to-End Response Time

## Technical Requirements

### System Architecture

```
┌─────────────┐
│ Ring        │
│ Doorbell    │
└──────┬──────┘
       │ Webhook/Event
       ▼
┌─────────────────────────────────┐
│ Backend Service (FastAPI)       │
│                                  │
│  ┌─────────────────────────┐   │
│  │ Event Handler           │   │
│  └────────┬────────────────┘   │
│           │                     │
│  ┌────────▼──────────┐         │
│  │ ElevenLabs TTS    │         │
│  │ "Password?"       │         │
│  └────────┬──────────┘         │
│           │                     │
│  ┌────────▼──────────┐         │
│  │ Audio Playback    │         │
│  │ via Ring          │         │
│  └────────┬──────────┘         │
│           │                     │
│  ┌────────▼──────────┐         │
│  │ Audio Recording   │         │
│  │ (5-10 sec)        │         │
│  └────────┬──────────┘         │
│           │                     │
│  ┌────────▼──────────┐         │
│  │ Whisper/Deepgram  │         │
│  │ STT               │         │
│  └────────┬──────────┘         │
│           │                     │
│  ┌────────▼──────────┐         │
│  │ Fuzzy Password    │         │
│  │ Matcher           │         │
│  └────────┬──────────┘         │
│           │                     │
│  ┌────────▼──────────┐         │
│  │ Response Handler  │         │
│  │ (Accept/Reject)   │         │
│  └───────────────────┘         │
│                                  │
│  All operations traced to:      │
│  ┌─────────────────────────┐   │
│  │ Langfuse                │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

### Tech Stack

**Backend:**
- **Framework**: FastAPI (Python 3.11+)
- **Async**: asyncio/aiohttp for performant API calls
- **Web Server**: Uvicorn

**AI/ML Services:**
- **TTS**: ElevenLabs API
- **STT**: Whisper (OpenAI API) or Deepgram API
- **Fuzzy Matching**: rapidfuzz or jellyfish

**Monitoring:**
- **Tracing**: Langfuse SDK

**Ring Integration:**
- **Option 1**: `ring-doorbell` Python library (unofficial)
- **Option 2**: Home Assistant as middleware
- **Option 3**: IFTTT/Zapier Webhooks
- **⚠️ Note**: Ring has no official public API

**Hosting:**
- **Recommended**: Railway.app (~$5/month)
- **Alternative 1**: Render.com (Free Tier possible)
- **Alternative 2**: Digital Ocean Droplet ($4-6/month)
- **Alternative 3**: Raspberry Pi + ngrok/Tailscale (One-time ~€50)

### Configuration

**Environment Variables:**
```bash
# Ring API
RING_USERNAME=your_email@example.com
RING_PASSWORD=your_password
RING_2FA_TOKEN=optional

# ElevenLabs
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=witch_voice_id

# Speech-to-Text
OPENAI_API_KEY=your_key  # for Whisper
# OR
DEEPGRAM_API_KEY=your_key

# Langfuse
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Application
PASSWORDS=password1,password2,alohomora,mellon
FUZZY_THRESHOLD=80
RECORDING_DURATION=8
MAX_ATTEMPTS=3
```

### API Endpoints

```
POST /webhooks/ring/doorbell
- Receives Ring Doorbell Events
- Triggers entire workflow

GET /health
- Health Check Endpoint

POST /test/password
- Test endpoint for password matching
- Body: {"audio_url": "..."} or {"text": "..."}

GET /config/passwords
- List configured passwords (Admin-Only)

POST /config/passwords
- Add/remove passwords (Admin-Only)
```

## Workflow Details

### Happy Path

1. **Doorbell Event** → Backend receives webhook
2. **TTS Generation** → "Password?" with ElevenLabs (or pre-generated)
3. **Audio Playback** → Via Ring intercom
4. **Recording Start** → Record for 8 seconds
5. **STT Processing** → Transcription with Whisper/Deepgram
6. **Fuzzy Matching** → Compare with password list
7. **Match Found (>80%)** → Success message + instructions
8. **Trace Event** → Log all steps in Langfuse

### Edge Cases

**Wrong Password:**
- Response: "Wrong password. Try again!" (in witch voice)
- Max. 2-3 attempts
- After failed attempts: "Access denied!"
- Trace with failure reason

**No Audio Detected:**
- Response: "I didn't understand you. Please repeat!"
- Fallback after 2 attempts

**Service Error (STT/TTS down):**
- Fallback message: "System error. Please ring normally."
- Error trace in Langfuse

**Timeout:**
- After 30 seconds without response → End session
- Trace with timeout reason

## Security Considerations

1. **API Key Management**: All keys in Environment Variables, never in code
2. **Rate Limiting**: Max. 5 doorbell events per 10 minutes from same Ring ID
3. **Webhook Verification**: Validate Ring Webhook Signature
4. **Password Storage**: Not in plaintext in logs/traces
5. **Audio Storage**: Delete temporary audio files after processing
6. **HTTPS**: All webhook endpoints over HTTPS

## Performance Goals

- **TTS Generation**: < 2 seconds
- **STT Processing**: < 3 seconds
- **Fuzzy Matching**: < 100ms
- **End-to-End Response**: < 10 seconds (from doorbell to response)

## Open Questions / Decisions

### 1. Ring API Integration
- [ ] Which Ring hardware exactly? (Model?)
- [ ] Unofficial library vs. Home Assistant middleware?
- [ ] Webhooks possible or polling necessary?

### 2. Audio Handling
- [ ] Pre-generate witch voice audio files or on-demand?
- [ ] Audio format from Ring (mp3, wav, opus)?
- [ ] Streaming or complete download?

### 3. Password Management
- [ ] How many passwords initially?
- [ ] Should passwords be stored phonetically?
- [ ] Admin interface for password management needed?

### 4. Multi-Language Support
- [ ] German only or also English?
- [ ] Language detection for STT?

### 5. Testing Strategy
- [ ] Mock Ring events for local development?
- [ ] Prepare audio test files?

## Next Steps

1. Research Ring API possibilities
2. Set up project structure
3. First prototypes for individual components
4. Integration testing
5. Prepare deployment

## Success Metrics

- **Functionality**: 95%+ correct password recognition
- **Performance**: < 10 seconds response time
- **Reliability**: 99%+ uptime
- **User Experience**: Guest excitement! 🧙‍♀️
