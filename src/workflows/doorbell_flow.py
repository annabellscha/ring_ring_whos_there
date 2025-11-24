"""
Complete doorbell workflow orchestration.
Handles the full password authentication flow.
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

# Initialize Langfuse
langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


class DoorbellSession:
    """Manages state for a single doorbell interaction."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.attempts = 0
        self.max_attempts = settings.max_attempts
        self.start_time = time.time()
        self.transcriptions = []
        self.match_scores = []

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "duration_seconds": round(time.time() - self.start_time, 2),
            "transcriptions": self.transcriptions,
            "match_scores": self.match_scores,
        }


class DoorbellFlowOrchestrator:
    """Orchestrates the complete doorbell authentication flow."""

    def __init__(self):
        self.active_sessions: Dict[str, DoorbellSession] = {}

    async def handle_doorbell_event(self, device_id: str) -> dict:
        """
        Handle a complete doorbell event with password authentication.

        Args:
            device_id: Ring device ID

        Returns:
            Result dictionary with status and details
        """
        logger.info(f"🔔 Doorbell event started for device: {device_id}")

        # Create Langfuse trace for this doorbell event
        trace = langfuse.trace(
            name="doorbell_authentication",
            metadata={
                "device_id": device_id,
                "timestamp": time.time(),
            }
        )

        session = DoorbellSession(device_id)
        self.active_sessions[device_id] = session

        try:
            # Step 1: Play "Passwort?" greeting
            await self._play_greeting(device_id)

            # Step 2-4: Attempt password authentication (with retries)
            while session.attempts < session.max_attempts:
                session.attempts += 1
                logger.info(f"🔄 Attempt {session.attempts}/{session.max_attempts}")

                # Create a span for this attempt
                span = trace.span(
                    name=f"authentication_attempt_{session.attempts}",
                    metadata={"attempt": session.attempts}
                )

                # Record audio response
                audio_path = await self._record_response(device_id)
                if not audio_path:
                    await self._play_no_audio_message(device_id)
                    span.end(metadata={"status": "no_audio"})
                    continue

                # Transcribe audio (with tracing)
                start_time = time.time()
                transcription = await self._transcribe_audio(audio_path)
                stt_latency = time.time() - start_time
                session.transcriptions.append(transcription["text"])

                span.event(
                    name="stt_transcription",
                    metadata={
                        "text": transcription["text"],
                        "latency_ms": round(stt_latency * 1000, 2),
                        "mock": transcription.get("mock", False)
                    }
                )

                # Check password (with tracing)
                start_time = time.time()
                match, score, matched_password = self._check_password(
                    transcription["text"]
                )
                match_latency = time.time() - start_time
                session.match_scores.append(score)

                span.event(
                    name="password_match",
                    metadata={
                        "match": match,
                        "score": score,
                        "matched_password": matched_password,
                        "latency_ms": round(match_latency * 1000, 2)
                    }
                )

                if match:
                    # SUCCESS!
                    span.end(metadata={"status": "success", "score": score})
                    result = await self._handle_success(
                        device_id, session, matched_password, score
                    )

                    # Update trace with final result
                    trace.update(
                        output=result,
                        metadata={
                            **trace.get_trace_metadata(),
                            "status": "success",
                            "attempts": session.attempts,
                            "duration_ms": round((time.time() - session.start_time) * 1000, 2)
                        }
                    )

                    return result
                else:
                    # Wrong password
                    span.end(metadata={"status": "wrong_password", "score": score})
                    await self._handle_wrong_password(device_id, session)

            # Max attempts reached - DENIED
            result = await self._handle_access_denied(device_id, session)

            # Update trace with denied result
            trace.update(
                output=result,
                metadata={
                    "status": "denied",
                    "attempts": session.attempts,
                    "duration_ms": round((time.time() - session.start_time) * 1000, 2)
                }
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error in doorbell flow: {e}")
            await self._play_error_message(device_id)

            error_result = {
                "status": "error",
                "error": str(e),
                "session": session.to_dict(),
            }

            # Update trace with error
            trace.update(
                output=error_result,
                metadata={
                    "status": "error",
                    "error": str(e),
                    "duration_ms": round((time.time() - session.start_time) * 1000, 2)
                }
            )

            return error_result

        finally:
            # Cleanup session
            if device_id in self.active_sessions:
                del self.active_sessions[device_id]

    async def _play_greeting(self, device_id: str):
        """Play the initial 'Passwort?' greeting."""
        logger.info("🎭 Playing greeting: 'Passwort?'")
        audio_path = "audio_assets/witch_password.mp3"
        await mock_ring_service.play_audio(device_id, audio_path)
        await asyncio.sleep(0.5)  # Wait a bit after playing

    async def _record_response(self, device_id: str) -> Optional[str]:
        """Record the visitor's audio response."""
        logger.info("🎤 Recording response...")
        duration = settings.recording_duration
        audio_path = await mock_ring_service.record_audio(device_id, duration)
        return audio_path

    async def _transcribe_audio(self, audio_path: str) -> dict:
        """Transcribe the recorded audio."""
        logger.info("📝 Transcribing audio...")
        transcription = await stt_service.transcribe(audio_path)
        logger.info(f"   Transcribed: '{transcription['text']}'")
        return transcription

    def _check_password(self, text: str) -> tuple:
        """Check if transcribed text matches a password."""
        logger.info(f"🔍 Checking password: '{text}'")
        match, score, password = password_service.check_password(text)
        logger.info(f"   Match: {match}, Score: {score:.2f}%")
        return match, score, password

    async def _handle_success(
        self, device_id: str, session: DoorbellSession, password: str, score: float
    ) -> dict:
        """Handle successful password match."""
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

    async def _handle_wrong_password(self, device_id: str, session: DoorbellSession):
        """Handle wrong password attempt."""
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
        """Handle access denied after max attempts."""
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

    async def _play_no_audio_message(self, device_id: str):
        """Play message when no audio was detected."""
        logger.warning("⚠️  No audio detected")
        await mock_ring_service.play_audio(device_id, "audio_assets/witch_repeat.mp3")

    async def _play_error_message(self, device_id: str):
        """Play error message."""
        logger.error("⚠️  System error")
        # We don't have witch_error.mp3 with content, so use witch_denied
        await mock_ring_service.play_audio(device_id, "audio_assets/witch_denied.mp3")


# Global orchestrator instance
doorbell_orchestrator = DoorbellFlowOrchestrator()
