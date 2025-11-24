"""
Main FastAPI application for Ring Ring Who's There.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ring Ring Who's There",
    description="A magical door opening system with witch voice authentication",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ring Ring Who's There - Witch Voice Authentication System",
        "docs": "/docs",
        "test_endpoints": {
            "password": "POST /test/password",
            "mock_doorbell": "POST /test/doorbell",
        }
    }


@app.post("/test/password")
async def test_password_matching(text: str):
    """
    Test password matching with fuzzy logic.

    Args:
        text: The text to match against configured passwords

    Returns:
        Match result with score and matched password
    """
    from src.services.password_service import password_service

    match, score, matched_pw = password_service.check_password(text)

    return {
        "input": text,
        "match": match,
        "score": score,
        "matched_password": matched_pw,
        "threshold": password_service.threshold,
        "configured_passwords": password_service.passwords,
    }


@app.post("/test/doorbell")
async def test_mock_doorbell():
    """
    Simulate a doorbell press using the mock Ring service.

    Returns:
        Event simulation result
    """
    from src.services.mock_ring_service import mock_ring_service

    # Simulate doorbell press
    device_id = "mock-device-123"

    logger.info(f"Test endpoint: Simulating doorbell press on {device_id}")

    # Play mock audio
    await mock_ring_service.play_audio(device_id, "audio_assets/witch_password.mp3")

    # Record mock audio
    recorded_audio = await mock_ring_service.record_audio(device_id, duration=3)

    return {
        "status": "success",
        "message": "Mock doorbell event simulated",
        "device_id": device_id,
        "audio_played": "witch_password.mp3",
        "audio_recorded": recorded_audio,
        "note": "Check logs for detailed mock service output",
    }


@app.post("/test/complete-flow")
async def test_complete_flow():
    """
    Test the complete doorbell workflow end-to-end.

    This simulates:
    1. Doorbell press
    2. Playing "Passwort?" greeting
    3. Recording response (mock)
    4. Transcribing audio (mock)
    5. Password matching
    6. Response based on result

    Returns:
        Complete workflow result
    """
    from src.workflows.doorbell_flow import doorbell_orchestrator

    device_id = "mock-device-123"

    logger.info(f"🧪 Testing complete doorbell flow for {device_id}")

    result = await doorbell_orchestrator.handle_doorbell_event(device_id)

    logger.info(f"✅ Complete flow test finished: {result['status']}")

    return result


@app.post("/webhooks/ring/doorbell")
async def ring_doorbell_webhook(device_id: str = "mock-device-123"):
    """
    Webhook endpoint for Ring doorbell events.

    This would be called by Ring when someone presses the doorbell.
    For now, it works with mock Ring service.

    Args:
        device_id: Ring device ID (defaults to mock device)

    Returns:
        Workflow execution result
    """
    from src.workflows.doorbell_flow import doorbell_orchestrator

    logger.info(f"🔔 Webhook: Doorbell pressed on {device_id}")

    # Execute the complete doorbell workflow
    result = await doorbell_orchestrator.handle_doorbell_event(device_id)

    logger.info(f"Webhook result: {result['status']}")

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
    )
