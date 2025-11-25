"""
Main FastAPI application for Ring Ring Who's There.

This module provides the REST API interface for the doorbell authentication
system. It exposes endpoints for health checks, testing, and webhook handling
for Ring doorbell events.

Endpoints:
    GET  /                    - Root endpoint with API information
    GET  /health              - Health check endpoint
    POST /test/password       - Test password matching functionality
    POST /test/doorbell       - Test mock doorbell simulation
    POST /test/complete-flow  - Test complete authentication workflow
    POST /webhooks/ring/doorbell - Webhook for Ring doorbell events

Example:
    ```bash
    # Start the server
    uvicorn src.main:app --reload
    
    # Test password matching
    curl -X POST "http://localhost:8000/test/password?text=alohomora"
    
    # Trigger complete flow
    curl -X POST "http://localhost:8000/test/complete-flow"
    ```

See Also:
    src.workflows.doorbell_flow: Main workflow orchestration
    src.services.password_service: Password matching logic
"""

from fastapi import FastAPI, Query
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
async def health_check() -> dict:
    """
    Health check endpoint for monitoring and load balancers.

    Returns basic system status and version information. This endpoint
    should be used by monitoring systems to verify the service is running.

    Returns:
        Dictionary containing:
            - status: Always "healthy" if endpoint is reachable
            - environment: Current environment (development/production)
            - version: Application version string

    Example:
        ```bash
        curl http://localhost:8000/health
        # {"status": "healthy", "environment": "development", "version": "0.1.0"}
        ```
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
    }


@app.get("/")
async def root() -> dict:
    """
    Root endpoint providing API information and available endpoints.

    Returns a welcome message and information about available test endpoints
    and API documentation.

    Returns:
        Dictionary containing:
            - message: Welcome message
            - docs: Path to Swagger/OpenAPI documentation
            - test_endpoints: Dictionary mapping endpoint names to their paths

    Example:
        ```bash
        curl http://localhost:8000/
        ```
    """
    return {
        "message": "Ring Ring Who's There - Witch Voice Authentication System",
        "docs": "/docs",
        "test_endpoints": {
            "password": "POST /test/password",
            "mock_doorbell": "POST /test/doorbell",
            "complete_flow": "POST /test/complete-flow",
        }
    }


@app.post("/test/password")
async def test_password_matching(text: str = Query(..., description="Text to match against passwords")) -> dict:
    """
    Test password matching with fuzzy logic.

    This endpoint allows testing the password matching service without
    going through the full doorbell workflow. Useful for debugging and
    tuning fuzzy matching thresholds.

    Args:
        text: The text to match against configured passwords. This simulates
            what would be transcribed from a visitor's spoken response.

    Returns:
        Dictionary containing:
            - input: The input text that was tested
            - match: Boolean indicating if a match was found
            - score: Similarity score (0-100) for the best match
            - matched_password: The password that matched (if any)
            - threshold: The configured fuzzy matching threshold
            - configured_passwords: List of all configured passwords

    Example:
        ```bash
        curl -X POST "http://localhost:8000/test/password?text=alohomora"
        # {
        #   "input": "alohomora",
        #   "match": true,
        #   "score": 100.0,
        #   "matched_password": "alohomora",
        #   "threshold": 75,
        #   "configured_passwords": ["alohomora", "mellon", "open sesame"]
        # }
        ```

    Note:
        This endpoint uses the same password matching logic as the actual
        doorbell workflow, so results should be consistent.
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
async def test_mock_doorbell() -> dict:
    """
    Simulate a doorbell press using the mock Ring service.

    This endpoint tests basic Ring service functionality (audio playback
    and recording) without going through the full authentication workflow.
    Useful for verifying that the mock service is working correctly.

    Returns:
        Dictionary containing:
            - status: "success" if simulation completed
            - message: Description of what was simulated
            - device_id: The device ID used for simulation
            - audio_played: Filename of the audio that was played
            - audio_recorded: Path to the recorded audio file (if any)
            - note: Additional information about the simulation

    Example:
        ```bash
        curl -X POST http://localhost:8000/test/doorbell
        # {
        #   "status": "success",
        #   "message": "Mock doorbell event simulated",
        #   "device_id": "mock-device-123",
        #   "audio_played": "witch_password.mp3",
        #   "audio_recorded": "recordings/mock-device-123_...wav",
        #   "note": "Check logs for detailed mock service output"
        # }
        ```

    Note:
        This uses the mock Ring service, so no actual Ring device is involved.
        Check the application logs for detailed output from the mock service.
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
async def test_complete_flow() -> dict:
    """
    Test the complete doorbell workflow end-to-end.

    This endpoint simulates the entire doorbell authentication flow from
    start to finish, including:
    1. Doorbell press event
    2. Playing "Passwort?" greeting
    3. Recording visitor's audio response (mock)
    4. Transcribing audio to text (mock)
    5. Matching text against configured passwords
    6. Playing appropriate response (welcome/error/denial)

    This is the most comprehensive test endpoint and exercises all components
    of the system together.

    Returns:
        Dictionary with workflow result containing:
            - status: One of "success", "denied", or "error"
            - matched_password: The password that matched (if status is "success")
            - score: Match confidence score (if status is "success")
            - attempts: Number of password attempts made
            - session: Complete session state with transcriptions and scores
            - reason: Denial reason (if status is "denied")
            - error: Error message (if status is "error")

    Example:
        ```bash
        curl -X POST http://localhost:8000/test/complete-flow
        # {
        #   "status": "success",
        #   "matched_password": "alohomora",
        #   "score": 100.0,
        #   "attempts": 1,
        #   "session": {
        #     "device_id": "mock-device-123",
        #     "attempts": 1,
        #     "duration_seconds": 2.5,
        #     "transcriptions": ["alohomora"],
        #     "match_scores": [100.0]
        #   }
        # }
        ```

    Note:
        This uses mock services for Ring, STT, and audio recording, so it
        doesn't require actual hardware or API keys. All events are logged
        to Langfuse for observability.
    """
    from src.workflows.doorbell_flow import doorbell_orchestrator

    device_id = "mock-device-123"

    logger.info(f"🧪 Testing complete doorbell flow for {device_id}")

    result = await doorbell_orchestrator.handle_doorbell_event(device_id)

    logger.info(f"✅ Complete flow test finished: {result['status']}")

    return result


@app.post("/webhooks/ring/doorbell")
async def ring_doorbell_webhook(device_id: str = Query(default="mock-device-123", description="Ring device ID")) -> dict:
    """
    Webhook endpoint for Ring doorbell events.

    This endpoint is designed to be called by Ring's webhook system when
    a doorbell is pressed. It triggers the complete authentication workflow.
    Currently works with the mock Ring service for testing.

    In production, this would be configured in the Ring API settings to
    receive real-time doorbell press events.

    Args:
        device_id: The Ring device ID where the doorbell was pressed.
            Defaults to "mock-device-123" for testing.

    Returns:
        Dictionary with workflow execution result. See `test_complete_flow()`
        for the structure of the returned dictionary.

    Example:
        ```bash
        # Production webhook call (would come from Ring)
        curl -X POST "http://your-server.com/webhooks/ring/doorbell?device_id=doorbell-abc123"
        
        # Testing with mock device
        curl -X POST "http://localhost:8000/webhooks/ring/doorbell"
        ```

    Note:
        - In production, this endpoint should be secured with authentication
          to prevent unauthorized access.
        - The device_id parameter should be validated against known devices.
        - Consider rate limiting to prevent abuse.
        - All events are logged to Langfuse for observability and debugging.
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
