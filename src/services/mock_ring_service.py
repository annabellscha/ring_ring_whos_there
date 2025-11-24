"""
Mock Ring service for development and testing.
Simulates Ring doorbell behavior without actual hardware.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class MockRingService:
    """
    Mock Ring service that simulates doorbell events and audio operations.

    Usage:
        # Simulate a doorbell press
        await mock_ring.simulate_doorbell_press("mock-device-123")

        # Mock audio playback
        await mock_ring.play_audio("mock-device-123", "witch_password.mp3")

        # Mock audio recording (returns test audio file path)
        audio_path = await mock_ring.record_audio("mock-device-123", duration=8)
    """

    def __init__(self):
        self.authenticated = True
        self.devices = {
            "mock-device-123": {
                "name": "Front Door",
                "type": "doorbell",
                "battery_life": 85,
            }
        }
        self._event_callback = None
        logger.info("MockRingService initialized (development mode)")

    async def authenticate(self) -> bool:
        """Mock authentication - always succeeds."""
        logger.info("Mock: Authentication successful")
        await asyncio.sleep(0.1)  # Simulate network delay
        self.authenticated = True
        return True

    def set_event_callback(self, callback: Callable):
        """Set callback for doorbell events."""
        self._event_callback = callback
        logger.info("Event callback registered")

    async def simulate_doorbell_press(self, device_id: str = "mock-device-123"):
        """
        Simulate a doorbell press event.

        Args:
            device_id: Mock device ID
        """
        logger.info(f"🔔 Simulating doorbell press on {device_id}")

        if self._event_callback:
            event_data = {
                "event_type": "doorbell_pressed",
                "device_id": device_id,
                "device_name": self.devices[device_id]["name"],
                "timestamp": asyncio.get_event_loop().time(),
            }
            await self._event_callback(event_data)
        else:
            logger.warning("No event callback registered")

    async def play_audio(self, device_id: str, audio_file_path: str) -> bool:
        """
        Mock audio playback through Ring speaker.

        Args:
            device_id: Ring device ID
            audio_file_path: Path to audio file to play

        Returns:
            True (always succeeds in mock)
        """
        logger.info(f"🔊 Mock: Playing audio on {device_id}: {audio_file_path}")

        # Check if file exists
        if not Path(audio_file_path).exists():
            logger.warning(f"Audio file not found: {audio_file_path}")
            logger.info("   (This is OK in mock mode - audio would play if file existed)")

        # Simulate audio playback delay
        await asyncio.sleep(0.5)
        logger.info(f"✅ Mock: Audio playback complete")
        return True

    async def record_audio(
        self, device_id: str, duration: int = 8
    ) -> Optional[str]:
        """
        Mock audio recording from Ring microphone.
        Returns a path to a test audio file if available.

        Args:
            device_id: Ring device ID
            duration: Recording duration in seconds

        Returns:
            Path to test audio file, or None
        """
        logger.info(f"🎤 Mock: Recording audio from {device_id} for {duration}s")

        # Simulate recording delay
        await asyncio.sleep(duration * 0.1)  # 10% of actual duration for testing

        # Look for test audio files in audio_assets directory
        test_audio_dir = Path("audio_assets")

        # Try to find a test audio file
        test_files = []
        if test_audio_dir.exists():
            test_files = list(test_audio_dir.glob("test_*.mp3")) + \
                        list(test_audio_dir.glob("test_*.wav"))

        if test_files:
            test_file = test_files[0]
            logger.info(f"✅ Mock: Using test audio file: {test_file}")
            return str(test_file)
        else:
            logger.warning("No test audio files found in audio_assets/")
            logger.info("   Create test_password.mp3 in audio_assets/ to test STT")

            # Return a mock path (file doesn't exist yet)
            mock_path = "audio_assets/mock_recording.mp3"
            logger.info(f"   Returning mock path: {mock_path}")
            return mock_path

    async def get_devices(self):
        """Get list of mock devices."""
        logger.info("Mock: Fetching devices")
        await asyncio.sleep(0.1)
        return self.devices

    async def get_device_info(self, device_id: str):
        """Get mock device information."""
        logger.info(f"Mock: Getting info for device {device_id}")
        await asyncio.sleep(0.1)
        return self.devices.get(device_id)


# Global mock Ring service instance
mock_ring_service = MockRingService()


if __name__ == "__main__":
    # Test script for mock Ring service
    async def test_mock_ring():
        print("Testing Mock Ring Service\n")

        # Test authentication
        auth = await mock_ring_service.authenticate()
        print(f"Authentication: {auth}\n")

        # Test device listing
        devices = await mock_ring_service.get_devices()
        print(f"Devices: {devices}\n")

        # Test audio playback
        await mock_ring_service.play_audio(
            "mock-device-123",
            "audio_assets/witch_password.mp3"
        )
        print()

        # Test audio recording
        audio_path = await mock_ring_service.record_audio(
            "mock-device-123",
            duration=3
        )
        print(f"Recorded audio path: {audio_path}\n")

        # Test doorbell event
        def event_handler(event):
            print(f"Event received: {event}")

        mock_ring_service.set_event_callback(event_handler)
        await mock_ring_service.simulate_doorbell_press()

    asyncio.run(test_mock_ring())
