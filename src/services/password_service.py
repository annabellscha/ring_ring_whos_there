"""
Password matching service with fuzzy matching support.
Validates spoken passwords against configured password list.
"""

from rapidfuzz import fuzz, process
import jellyfish
import logging
from typing import Tuple, Optional

from src.config import settings

logger = logging.getLogger(__name__)


class PasswordService:
    """Password validation with fuzzy and phonetic matching."""

    def __init__(self, passwords: list[str] = None, threshold: int = None):
        self.passwords = passwords or settings.password_list
        self.threshold = threshold or settings.fuzzy_threshold
        logger.info(
            f"Initialized PasswordService with {len(self.passwords)} passwords, threshold: {self.threshold}"
        )

    def check_password(self, spoken_text: str) -> Tuple[bool, float, Optional[str]]:
        """
        Check if spoken text matches any configured password.

        Args:
            spoken_text: The transcribed text from speech-to-text

        Returns:
            Tuple of (match_found, similarity_score, matched_password)
        """
        if not spoken_text or not spoken_text.strip():
            logger.warning("Empty spoken text provided")
            return False, 0.0, None

        spoken_text = spoken_text.strip().lower()
        logger.info(f"Checking password for: '{spoken_text}'")

        # Try exact match first (case-insensitive)
        for password in self.passwords:
            if password.lower() == spoken_text:
                logger.info(f"Exact match found: {password}")
                return True, 100.0, password

        # Fuzzy matching with rapidfuzz
        best_match = self._fuzzy_match(spoken_text)
        if best_match:
            match, score, password = best_match
            if score >= self.threshold:
                logger.info(
                    f"Fuzzy match found: '{password}' (score: {score:.2f})"
                )
                return True, score, password

        # Phonetic matching as fallback
        phonetic_match = self._phonetic_match(spoken_text)
        if phonetic_match:
            match, score, password = phonetic_match
            if score >= self.threshold:
                logger.info(
                    f"Phonetic match found: '{password}' (score: {score:.2f})"
                )
                return True, score, password

        logger.info(f"No match found for: '{spoken_text}'")
        return False, best_match[1] if best_match else 0.0, None

    def _fuzzy_match(self, spoken_text: str) -> Optional[Tuple[bool, float, str]]:
        """Perform fuzzy matching using Levenshtein distance."""
        passwords_lower = [p.lower() for p in self.passwords]

        # Use rapidfuzz to find best match
        result = process.extractOne(
            spoken_text,
            passwords_lower,
            scorer=fuzz.ratio,
        )

        if result:
            matched_lower, score, index = result
            original_password = self.passwords[index]
            return True, score, original_password

        return None

    def _phonetic_match(self, spoken_text: str) -> Optional[Tuple[bool, float, str]]:
        """Perform phonetic matching using Metaphone algorithm."""
        spoken_metaphone = jellyfish.metaphone(spoken_text)

        best_score = 0.0
        best_password = None

        for password in self.passwords:
            password_metaphone = jellyfish.metaphone(password.lower())

            # Calculate similarity between metaphone codes
            if spoken_metaphone == password_metaphone:
                # Exact phonetic match
                score = 100.0
            else:
                # Use Levenshtein on metaphone codes
                score = fuzz.ratio(spoken_metaphone, password_metaphone)

            if score > best_score:
                best_score = score
                best_password = password

        if best_password and best_score > 0:
            return True, best_score, best_password

        return None


# Global password service instance
password_service = PasswordService()


if __name__ == "__main__":
    # Test script for password matching
    test_cases = [
        ("alohomora", True),
        ("alo mora", True),  # Space variation
        ("alohomorra", True),  # Typo
        ("mellon", True),
        ("melon", True),  # Phonetically similar
        ("open sesame", True),
        ("open sesami", True),  # Typo
        ("random nonsense", False),
        ("", False),
    ]

    print(f"Testing with passwords: {password_service.passwords}")
    print(f"Threshold: {password_service.threshold}\n")

    for spoken, should_match in test_cases:
        match, score, password = password_service.check_password(spoken)
        status = "✓" if match == should_match else "✗"
        print(
            f"{status} '{spoken}' -> Match: {match}, Score: {score:.2f}, Password: {password}"
        )
