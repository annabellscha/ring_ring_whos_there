"""
Complete doorbell workflow orchestration.

This module implements the main doorbell authentication workflow that orchestrates
the entire interaction flow from doorbell press to access grant/denial. It manages
sessions, coordinates between services (TTS, STT, password matching), handles
retries, and logs events to Langfuse for observability.

Workflow Steps:
    1. Doorbell press detected
    2. Play greeting ("Passwort?")
    3. Record visitor's audio response
    4. Transcribe audio to text
    5. Match text against configured passwords
    6. If match: Play welcome message and grant access
    7. If no match: Play error message and retry (up to max_attempts)
    8. If max attempts exceeded: Play denial message

Example:
    ```python
    from src.workflows.doorbell_flow import doorbell_orchestrator
    
    result = await doorbell_orchestrator.handle_doorbell_event("doorbell-123")
    if result["status"] == "success":
        print("Access granted!")
    ```

See Also:
    src.services.mock_ring_service: Mock Ring service for testing
    src.services.tts_service: Text-to-speech service
    src.services.stt_service: Speech-to-text service
    src.services.password_service: Password matching service
"""

import asyncio
import logging
import time
from typing import Dict, Optional
from pathlib import Path

from src.services.mock_ring_service import mock_ring_service
from src.services.tts_service import tts_service
from src.services.stt_service import stt_service
from src.services.password_service import password_service
from src.config import settings

# Import Langfuse directly
from langfuse import Langfuse

logger = logging.getLogger(__name__)

# Initialize Langfuse for observability and tracing
langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


class DoorbellSession:
    """
    Manages state for a single doorbell interaction session.
    
    Tracks all relevant information about a doorbell authentication attempt,
    including attempts made, transcriptions received, match scores, and timing
    information. This data is used for logging, debugging, and observability.
    
    Attributes:
        device_id (str): The Ring device ID for this session.
        attempts (int): Number of password attempts made so far.
        max_attempts (int): Maximum number of attempts allowed.
        start_time (float): Unix timestamp when the session started.
        transcriptions (list[str]): List of all transcriptions received.
        match_scores (list[float]): List of match scores for each attempt.
    """

    def __init__(self, device_id: str):
        """
        Initialize a new doorbell session.

        Args:
            device_id: The Ring device ID that triggered this session.
        """
        self.device_id = device_id
        self.attempts = 0
        self.max_attempts = settings.max_attempts
        self.start_time = time.time()
        self.transcriptions = []
        self.match_scores = []

    def to_dict(self) -> dict:
        """
        Convert session state to a dictionary for logging/API responses.

        Returns:
            Dictionary containing all session state including:
                - device_id: The device ID
                - attempts: Number of attempts made
                - max_attempts: Maximum attempts allowed
                - duration_seconds: Total session duration
                - transcriptions: List of all transcriptions
                - match_scores: List of all match scores
        """
        return {
            "device_id": self.device_id,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "duration_seconds": round(time.time() - self.start_time, 2),
            "transcriptions": self.transcriptions,
            "match_scores": self.match_scores,
        }


class DoorbellFlowOrchestrator:
    """
    Orchestrates the complete doorbell authentication flow.
    
    This class coordinates all services involved in the doorbell authentication
    process, manages session state, handles retries, and provides observability
    through Langfuse logging. It implements the complete workflow from doorbell
    press to access grant/denial.
    
    Attributes:
        active_sessions (Dict[str, DoorbellSession]): Dictionary mapping device
            IDs to their active sessions. Used to track multiple concurrent
            doorbell interactions.
    """

    def __init__(self):
        """Initialize the orchestrator with an empty session dictionary."""
        self.active_sessions: Dict[str, DoorbellSession] = {}

    async def handle_doorbell_event(self, device_id: str) -> dict:
        """
        Handle a complete doorbell event with password authentication.

        This is the main entry point for doorbell events. It orchestrates the
        entire authentication flow:
        1. Creates a session to track the interaction
        2. Plays greeting message
        3. Records and transcribes visitor responses
        4. Validates passwords with fuzzy matching
        5. Handles retries up to max_attempts
        6. Grants access on success or denies after max attempts
        7. Logs all events to Langfuse for observability

        Args:
            device_id: The Ring device ID where the doorbell was pressed.
                Used to identify which device to interact with.

        Returns:
            Dictionary with the following structure:
                - status (str): One of "success", "denied", or "error"
                - matched_password (str, optional): The password that matched
                    (only present if status is "success")
                - score (float, optional): Match confidence score
                    (only present if status is "success")
                - attempts (int): Number of attempts made
                - session (dict): Complete session state
                - reason (str, optional): Denial reason (only if status is "denied")
                - error (str, optional): Error message (only if status is "error")

        Raises:
            Exception: If any step in the workflow fails unexpectedly. The
                error is caught, logged, and returned in the result dictionary.

        Example:
            ```python
            result = await orchestrator.handle_doorbell_event("doorbell-123")
            
            if result["status"] == "success":
                print(f"Access granted! Password: {result['matched_password']}")
            elif result["status"] == "denied":
                print(f"Access denied after {result['attempts']} attempts")
            ```

        Note:
            All events are logged to Langfuse for observability, including:
            - Doorbell event start
            - STT transcription latency and results
            - Password match scores
            - Authentication success/failure
        """
        logger.info(f"🔔 Doorbell event started for device: {device_id}")

        # TODO: Add Langfuse tracing once API documentation is verified
        # The Langfuse Python SDK API has changed between versions
        # Need to verify correct method signatures for trace/span/score

        session = DoorbellSession(device_id)
        self.active_sessions[device_id] = session

        try:
            # Step 1: Play "Passwort?" greeting
            await self._play_greeting(device_id)

            # Step 2-4: Attempt password authentication (with retries)
            while session.attempts < session.max_attempts:
                session.attempts += 1
                logger.info(f"🔄 Attempt {session.attempts}/{session.max_attempts}")

                # Record audio response
                audio_path = await self._record_response(device_id)
                if not audio_path:
                    await self._play_no_audio_message(device_id)
                    continue

                # Transcribe audio (with tracing)
                start_time = time.time()
                transcription = await self._transcribe_audio(audio_path)
                stt_latency = time.time() - start_time
                session.transcriptions.append(transcription["text"])

                # TODO: Log STT latency to Langfuse
                logger.debug(f"STT latency: {stt_latency:.3f}s")

                # Check password (with tracing)
                start_time = time.time()
                match, score, matched_password = self._check_password(
                    transcription["text"]
                )
                match_latency = time.time() - start_time
                session.match_scores.append(score)

                # TODO: Log password match to Langfuse
                logger.debug(f"Password match latency: {match_latency:.3f}s")

                if match:
                    # SUCCESS!
                    result = await self._handle_success(
                        device_id, session, matched_password, score
                    )

                    # TODO: Log success to Langfuse
                    logger.info(f"Authentication success logged (Langfuse integration pending)")

                    return result
                else:
                    # Wrong password
                    await self._handle_wrong_password(device_id, session)

            # Max attempts reached - DENIED
            result = await self._handle_access_denied(device_id, session)

            # TODO: Log denial to Langfuse
            logger.info(f"Authentication denial logged (Langfuse integration pending)")

            return result

        except Exception as e:
            logger.error(f"❌ Error in doorbell flow: {e}")
            await self._play_error_message(device_id)

            error_result = {
                "status": "error",
                "error": str(e),
                "session": session.to_dict(),
            }

            # TODO: Log error to Langfuse
            logger.error(f"Authentication error logged (Langfuse integration pending)")

            return error_result

        finally:
            # Cleanup session
            if device_id in self.active_sessions:
                del self.active_sessions[device_id]

    async def _play_greeting(self, device_id: str) -> None:
        """
        Play the initial 'Passwort?' greeting to the visitor.

        Args:
            device_id: The Ring device ID to play audio on.
        """
        logger.info("🎭 Playing greeting: 'Passwort?'")
        audio_path = "audio_assets/witch_password.mp3"
        await mock_ring_service.play_audio(device_id, audio_path)
        await asyncio.sleep(0.5)  # Wait a bit after playing

    async def _record_response(self, device_id: str) -> Optional[str]:
        """
        Record the visitor's audio response after the greeting.

        Args:
            device_id: The Ring device ID to record from.

        Returns:
            Path to the recorded audio file, or None if recording failed.
        """
        logger.info("🎤 Recording response...")
        duration = settings.recording_duration
        audio_path = await mock_ring_service.record_audio(device_id, duration)
        return audio_path

    async def _transcribe_audio(self, audio_path: str) -> dict:
        """
        Transcribe the recorded audio to text using STT service.

        Args:
            audio_path: Path to the audio file to transcribe.

        Returns:
            Dictionary containing transcription results with 'text' key.

        Raises:
            Exception: If transcription fails.
        """
        logger.info("📝 Transcribing audio...")
        transcription = await stt_service.transcribe(audio_path)
        logger.info(f"   Transcribed: '{transcription['text']}'")
        return transcription

    def _check_password(self, text: str) -> tuple[bool, float, Optional[str]]:
        """
        Check if transcribed text matches any configured password.

        Args:
            text: The transcribed text to check.

        Returns:
            Tuple of (match_found, similarity_score, matched_password).
            - match_found: True if a match was found above threshold
            - similarity_score: Confidence score (0-100)
            - matched_password: The password that matched, or None
        """
        logger.info(f"🔍 Checking password: '{text}'")
        match, score, password = password_service.check_password(text)
        logger.info(f"   Match: {match}, Score: {score:.2f}%")
        return match, score, password

    async def _handle_success(
        self, device_id: str, session: DoorbellSession, password: str, score: float
    ) -> dict:
        """
        Handle successful password match and grant access.

        Plays the welcome message and returns a success result dictionary.

        Args:
            device_id: The Ring device ID.
            session: The current doorbell session.
            password: The password that was matched.
            score: The confidence score of the match.

        Returns:
            Dictionary with status "success" and relevant details.
        """
        logger.info(f"✅ SUCCESS! Password '{password}' matched with {score:.2f}% confidence")

        # Play welcome message
        await mock_ring_service.play_audio(device_id, "audio_assets/witch_welcome.mp3")

        result = {
            "status": "success",
            "matched_password": password,
            "score": score,
            "attempts": session.attempts,
            "session": session.to_dict(),
        }

        logger.info(f"✅ Access granted after {session.attempts} attempt(s)")
        return result

    async def _handle_wrong_password(self, device_id: str, session: DoorbellSession) -> None:
        """
        Handle wrong password attempt with appropriate feedback.

        Plays error messages and prompts for retry if attempts remain.

        Args:
            device_id: The Ring device ID.
            session: The current doorbell session.
        """
        logger.warning(f"❌ Wrong password (attempt {session.attempts}/{session.max_attempts})")

        if session.attempts < session.max_attempts:
            # Not last attempt - ask to try again
            await mock_ring_service.play_audio(device_id, "audio_assets/witch_wrong.mp3")
            await asyncio.sleep(0.5)
            await mock_ring_service.play_audio(device_id, "audio_assets/witch_repeat.mp3")
        else:
            # Last attempt failed - will be denied
            pass

    async def _handle_access_denied(self, device_id: str, session: DoorbellSession) -> dict:
        """
        Handle access denied after maximum attempts exceeded.

        Plays denial message and returns denial result dictionary.

        Args:
            device_id: The Ring device ID.
            session: The current doorbell session.

        Returns:
            Dictionary with status "denied" and relevant details.
        """
        logger.error(f"🚫 ACCESS DENIED after {session.attempts} attempts")

        # Play access denied message
        await mock_ring_service.play_audio(device_id, "audio_assets/witch_denied.mp3")

        result = {
            "status": "denied",
            "reason": "max_attempts_exceeded",
            "attempts": session.attempts,
            "session": session.to_dict(),
        }

        return result

    async def _play_no_audio_message(self, device_id: str) -> None:
        """
        Play message when no audio was detected in the recording.

        Args:
            device_id: The Ring device ID to play audio on.
        """
        logger.warning("⚠️  No audio detected")
        await mock_ring_service.play_audio(device_id, "audio_assets/witch_repeat.mp3")

    async def _play_error_message(self, device_id: str) -> None:
        """
        Play error message when a system error occurs.

        Args:
            device_id: The Ring device ID to play audio on.
        """
        logger.error("⚠️  System error")
        # We don't have witch_error.mp3 with content, so use witch_denied
        await mock_ring_service.play_audio(device_id, "audio_assets/witch_denied.mp3")


# Global orchestrator instance
doorbell_orchestrator = DoorbellFlowOrchestrator()
