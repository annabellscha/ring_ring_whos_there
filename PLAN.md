# Implementation Plan - Ring Ring Who's There

## Overview

This plan describes the step-by-step implementation of the system in meaningful, testable phases.

## Phase 0: Setup & Research (Day 1)

### 0.1 Project Setup
- [x] Git repository initialized
- [x] Specs documented
- [ ] Create Python virtual environment
- [ ] `requirements.txt` with dependencies
- [ ] `.env.example` for configuration
- [ ] Set up basic project structure

### 0.2 Ring API Research
**Goal**: Figure out how we can communicate with Ring

**Approaches to investigate:**
1. **ring-doorbell** Python Library
   - Test: Installation & Authentication
   - Test: Doorbell Event Listening
   - Test: Two-way Audio (Playback & Recording)

2. **Home Assistant Integration**
   - Test: Ring Integration in HA
   - Test: Webhook/Event forwarding to our service
   - Evaluation: Additional complexity vs. stability

3. **IFTTT/Zapier**
   - Test: Ring Trigger to Webhook
   - Limitation: Probably no audio access

**Deliverable**:
- Document: `RING_API_RESEARCH.md` with pros/cons of each option
- Decision on one approach

### 0.3 Get API Keys
- [ ] ElevenLabs account + API Key
- [ ] OpenAI account + API Key (for Whisper)
- [ ] Langfuse account + Public/Secret Keys
- [ ] All keys in `.env` (don't commit!)

**Project Structure:**
```
ring_ring_whos_there/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI App
│   ├── config.py            # Config & Environment Variables
│   ├── models.py            # Pydantic Models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ring_service.py       # Ring API Integration
│   │   ├── tts_service.py        # ElevenLabs TTS
│   │   ├── stt_service.py        # Whisper/Deepgram STT
│   │   ├── password_service.py   # Fuzzy Matching
│   │   └── tracing_service.py    # Langfuse
│   ├── webhooks/
│   │   ├── __init__.py
│   │   └── ring_webhook.py       # Webhook Handler
│   └── utils/
│       ├── __init__.py
│       └── audio_utils.py        # Audio Processing
├── tests/
│   ├── __init__.py
│   ├── test_password_matching.py
│   ├── test_tts.py
│   └── test_stt.py
├── audio_assets/
│   └── witch_password.mp3        # Pre-generated "Password?"
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── SPECS.md
└── PLAN.md
```

---

## Phase 1: Standalone Services (Day 1-2)

**Strategy**: Develop and test each component individually, independent of Ring

### 1.1 ElevenLabs TTS Service
**File**: `src/services/tts_service.py`

**Features**:
- Connect to ElevenLabs API
- Generate Text → Audio with witch voice
- Save audio file (mp3)
- Pre-generate "Password?", "Welcome!", "Wrong password", etc.

**Test Script**: `python -m src.services.tts_service --text "Password?"`

**Deliverable**:
- Working TTS Service
- 5-10 pre-generated audio files in `audio_assets/`

### 1.2 Whisper STT Service
**File**: `src/services/stt_service.py`

**Features**:
- Transcribe Audio file (mp3/wav) → Text
- OpenAI Whisper API Integration
- Language Detection (de/en)
- Return confidence score

**Test Script**:
```bash
# Record your own voice and test
python -m src.services.stt_service --audio test_audio.mp3
```

**Deliverable**: Working STT Service with test audio files

### 1.3 Fuzzy Password Matcher
**File**: `src/services/password_service.py`

**Features**:
- Load list of passwords from config
- Fuzzy matching with `rapidfuzz`
- Configurable threshold (default: 80%)
- Phonetic matching option with `jellyfish`
- Return: (match: bool, score: float, matched_password: str)

**Test Cases**:
```python
test_cases = [
    ("alohomora", "alo mora", True),    # Space
    ("mellon", "melon", True),          # Phonetically similar
    ("open sesame", "open sesami", True),  # Typo
    ("random words", None, False)       # No match
]
```

**Deliverable**:
- Password Service with unit tests
- Test report with different thresholds

### 1.4 Langfuse Tracing Setup
**File**: `src/services/tracing_service.py`

**Features**:
- Initialize Langfuse SDK
- Decorator for function tracing
- Log custom events
- Metadata (latency, success/failure, scores)

**Test**:
```python
@trace_function("test_operation")
def test_operation():
    return "success"
```

**Deliverable**: Working tracing with test traces in Langfuse dashboard

---

## Phase 2: Backend API (Day 2-3)

### 2.1 FastAPI Basic Setup
**File**: `src/main.py`

**Features**:
- Initialize FastAPI app
- Health Check Endpoint: `GET /health`
- CORS Configuration
- Error Handling Middleware
- Logging Setup

**Test**: `curl http://localhost:8000/health`

### 2.2 Config Management
**File**: `src/config.py`

**Features**:
- Load `.env` file with `python-dotenv`
- Pydantic Settings for type safety
- Passwords from environment or config file
- Validation for API keys

```python
class Settings(BaseSettings):
    elevenlabs_api_key: str
    openai_api_key: str
    langfuse_public_key: str
    langfuse_secret_key: str
    passwords: list[str]
    fuzzy_threshold: int = 80
    recording_duration: int = 8
    max_attempts: int = 3
```

### 2.3 Test Endpoint for Password Matching
**Endpoint**: `POST /test/password`

**Request**:
```json
{
  "text": "alohomora"
}
```

**Response**:
```json
{
  "match": true,
  "score": 100.0,
  "matched_password": "alohomora",
  "timestamp": "2025-11-21T10:30:00Z"
}
```

**Deliverable**: API for manual testing of services

---

## Phase 3: Ring Integration (Day 3-4)

**⚠️ Critical Path - depends on research from Phase 0.2**

### 3.1 Ring Service Implementation
**File**: `src/services/ring_service.py`

**Features** (depends on chosen method):
- Authentication with Ring API
- Listen to doorbell events
- Audio playback via Ring speaker
- Audio recording from Ring microphone
- Webhook setup (if supported)

### 3.2 Ring Webhook Endpoint
**File**: `src/webhooks/ring_webhook.py`
**Endpoint**: `POST /webhooks/ring/doorbell`

**Request** (hypothetical):
```json
{
  "event_type": "doorbell_pressed",
  "device_id": "abc123",
  "timestamp": "2025-11-21T10:30:00Z",
  "video_url": "...",
  "audio_stream_url": "..."
}
```

**Handler Logic**:
1. Validate webhook signature
2. Extract device ID
3. Start doorbell flow (see Phase 4)

### 3.3 Mock Ring Service (for Testing)
**File**: `src/services/mock_ring_service.py`

**Purpose**: Development without real Ring hardware

**Features**:
- Simulate doorbell event
- Fake audio playback (log only)
- Return test audio file for STT

**Deliverable**:
- Testable integration without hardware
- Documentation on how to integrate real Ring API

---

## Phase 4: Main Workflow Integration (Day 4-5)

### 4.1 Doorbell Flow Orchestration
**File**: `src/workflows/doorbell_flow.py`

**Complete Workflow**:
```python
@trace_function("doorbell_flow")
async def handle_doorbell_event(device_id: str):
    # 1. Log Event
    logger.info(f"Doorbell pressed: {device_id}")

    # 2. Play "Password?" Audio
    await ring_service.play_audio(device_id, "witch_password.mp3")

    # 3. Record Audio (8 seconds)
    audio_file = await ring_service.record_audio(device_id, duration=8)

    # 4. Transcribe with Whisper
    transcription = await stt_service.transcribe(audio_file)

    # 5. Fuzzy Match Password
    match, score, matched_pw = password_service.check_password(transcription)

    # 6. Respond
    if match:
        await ring_service.play_audio(device_id, "witch_welcome.mp3")
        return {"status": "success", "score": score}
    else:
        await ring_service.play_audio(device_id, "witch_wrong_password.mp3")
        return {"status": "denied", "score": score}
```

### 4.2 Retry Logic
- Max. 3 attempts for wrong password
- After 3 failed attempts: Final rejection
- Session management (state for each doorbell event)

### 4.3 Error Handling
- Timeout after 30 seconds
- Fallback for service errors
- Graceful degradation

**Deliverable**: End-to-end workflow works (with mock or real Ring)

---

## Phase 5: Testing & Refinement (Day 5-6)

### 5.1 Integration Tests
**File**: `tests/test_integration.py`

**Test Cases**:
- [ ] Complete happy path
- [ ] Wrong password → Retry
- [ ] 3x wrong password → Rejection
- [ ] No audio detected → Error handling
- [ ] Service timeout → Fallback
- [ ] Concurrent doorbell events

### 5.2 Audio Quality Testing
- [ ] Simulate different microphone qualities
- [ ] Background noise handling
- [ ] Test accents/dialects

### 5.3 Performance Testing
- [ ] Latency measurement for each step
- [ ] End-to-end < 10 seconds?
- [ ] Analyze Langfuse traces

### 5.4 Security Audit
- [ ] API keys not in logs
- [ ] Webhook signature verification
- [ ] Rate limiting works
- [ ] HTTPS enforcement

**Deliverable**: Test report with all metrics

---

## Phase 6: Deployment (Day 6-7)

### 6.1 Deployment Configuration
**Railway.app / Render.com**

**Files**:
- `Procfile`: `web: uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- `railway.json` or `render.yaml`
- `Dockerfile` (optional, for Docker-based deploy)

### 6.2 Environment Variables Setup
- [ ] Add all secrets in platform
- [ ] Configure webhook URL
- [ ] Verify health check endpoint

### 6.3 Production Testing
- [ ] Deploy to staging
- [ ] Test with real Ring device
- [ ] Monitor logs & traces in Langfuse
- [ ] Performance under real-world conditions

### 6.4 Monitoring Setup
- [ ] Uptime monitoring (UptimeRobot, Better Stack)
- [ ] Error alerting
- [ ] Langfuse dashboard for analytics

**Deliverable**: Live system with monitoring

---

## Phase 7: Enhancements (Optional)

### 7.1 Admin Interface
- Web UI for password management
- Visualize Langfuse traces
- Listen to audio logs

### 7.2 Multi-Language Support
- German + English
- Language detection

### 7.3 Extended Features
- Video frame capture for face recognition
- Multi-user with different access levels
- Time-based passwords (daily rotation)

### 7.4 Voice Customization
- Different voices selectable
- Custom messages via admin UI

---

## Risks & Mitigation

### Risk 1: Ring API Instability
**Probability**: High (unofficial API)
**Impact**: Critical
**Mitigation**:
- Home Assistant as stable middleware
- Fallback to IFTTT for basic functionality
- Regular API testing

### Risk 2: Audio Quality
**Probability**: Medium
**Impact**: High (password recognition fails)
**Mitigation**:
- Low fuzzy threshold (75-80%)
- Additional phonetic matching
- Retry mechanism

### Risk 3: Latency > 10 Seconds
**Probability**: Medium
**Impact**: Medium (poor UX)
**Mitigation**:
- Pre-generated TTS audio files
- Parallel API calls where possible
- Caching

### Risk 4: Costs (API Calls)
**Probability**: Low
**Impact**: Low
**Mitigation**:
- Pre-generated audio reduces ElevenLabs calls
- Whisper API is cheap (~$0.006/minute)
- Rate limiting against abuse

---

## Success Criteria

- [ ] System responds to real doorbell events
- [ ] Witch voice plays correctly
- [ ] Password recognition ≥ 90% accuracy
- [ ] End-to-end response < 10 seconds
- [ ] All traces visible in Langfuse
- [ ] Zero downtime over 24 hours
- [ ] At least 5 successful real-world tests

---

## Timeline Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 0 | 4-6 hours | None |
| Phase 1 | 6-8 hours | Phase 0.3 |
| Phase 2 | 3-4 hours | Phase 1 |
| Phase 3 | 6-12 hours | Phase 0.2 (critical!) |
| Phase 4 | 4-6 hours | Phase 1, 2, 3 |
| Phase 5 | 4-6 hours | Phase 4 |
| Phase 6 | 3-4 hours | Phase 5 |

**Total**: 30-46 hours (~5-7 working days)

**Critical Path**: Phase 0.2 (Ring API Research) → Phase 3 → Phase 4

---

## Next Step

**Recommendation**: Start with **Phase 0** (Setup & Research)

1. Project Setup (30 min)
2. Ring API Research (2-3 hours) ← **Most important task!**
3. Get API keys (30 min)

**Ready to start?** 🚀
