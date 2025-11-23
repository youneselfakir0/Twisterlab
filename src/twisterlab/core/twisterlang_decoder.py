#!/usr/bin/env python3
"""
TwisterLang Decoder - Communication Optimization Module
Decodes TwisterLang messages back to natural language
"""

import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from .twisterlang_encoder import TwisterLangEncoder


class TwisterLangDecoder:
    def __init__(self, vocab_file: str = "twisterlang_vocab.json"):
        self.vocab_file = Path(vocab_file)
        self.encoder = TwisterLangEncoder(vocab_file)
        self.fallback_messages = {}  # Store original messages for verification

    def decode_message(
        self, encoded_message: str, verify_hash: bool = True
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Decode a TwisterLang message back to natural language
        Returns: (decoded_message, is_valid, error_message)
        """
        try:
            # Parse TwisterLang format: TLG::<code>::<hash>::<timestamp>
            if not encoded_message.startswith("TLG::"):
                return encoded_message, False, "Invalid TwisterLang format"

            parts = encoded_message.split("::")
            if len(parts) != 4:
                return encoded_message, False, "Malformed TwisterLang message"

            _, code, message_hash, timestamp_str = parts

            # Find the code in vocabulary
            decoded_message = self._lookup_code(code)
            if decoded_message is None:
                # Try fallback to original message if available
                fallback = self.fallback_messages.get(encoded_message)
                if fallback:
                    return fallback, True, None
                return encoded_message, False, f"Unknown code: {code}"

            # Verify hash if requested
            if verify_hash:
                # First try with decoded message
                msg_bytes = decoded_message.lower().encode()
                full_hash = hashlib.sha256(msg_bytes).hexdigest()
                expected_hash = full_hash[:8].upper()

                if expected_hash != message_hash:
                    # Try fallback to original message if available
                    fallback = self.fallback_messages.get(encoded_message)
                    if fallback:
                        fallback_bytes = fallback.lower().encode()
                        full_fallback_hash = hashlib.sha256(fallback_bytes).hexdigest()
                        fallback_hash = full_fallback_hash[:8].upper()
                        if fallback_hash == message_hash:
                            return fallback, True, None

                    error_msg = f"Hash mismatch: expected {expected_hash}, " f"got {message_hash}"
                    return decoded_message, False, error_msg

            # Verify timestamp (not too old, not in future)
            try:
                timestamp = int(timestamp_str)
                current_time = int(time.time())
                # Allow messages up to 1 hour old, but not from future
                # Allow messages up to 1 hour old, not from future
                tolerance = 60  # 1 minute tolerance for future
                if timestamp > current_time + tolerance:
                    return decoded_message, False, "Message from future"
                if current_time - timestamp > 3600 * 24:  # 24 hours max age
                    return decoded_message, False, "Message too old"
            except ValueError:
                return decoded_message, False, "Invalid timestamp"

            return decoded_message, True, None

        except Exception as e:
            return encoded_message, False, f"Decode error: {str(e)}"

    def _lookup_code(self, code: str) -> Optional[str]:
        """Look up a code in the vocabulary"""
        for key, data in self.encoder.vocab.items():
            if data.get("code") == code:
                return key.replace("_", " ").title()

        return None

    def store_fallback(self, encoded_message: str, original_message: str) -> None:
        """Store original message for fallback decoding"""
        self.fallback_messages[encoded_message] = original_message

        # Clean old fallbacks (keep only last 100)
        if len(self.fallback_messages) > 100:
            # Remove oldest entries
            items = list(self.fallback_messages.items())
            self.fallback_messages = dict(items[-100:])

    def get_vocab_info(self, code: str) -> Optional[Dict]:
        """Get information about a code from vocabulary"""
        for key, data in self.encoder.vocab.items():
            if data.get("code") == code:
                return {
                    "key": key,
                    "code": code,
                    "category": data.get("category"),
                    "priority": data.get("priority"),
                    "aliases": data.get("aliases", []),
                    "first_seen": data.get("first_seen"),
                }
        return None

    def validate_message_chain(self, messages: list) -> Dict:
        """Validate a chain of TwisterLang messages"""
        results = {
            "total_messages": len(messages),
            "valid_messages": 0,
            "invalid_messages": 0,
            "errors": [],
            "categories": {},
            "priorities": {"low": 0, "medium": 0, "high": 0, "critical": 0},
        }

        for msg in messages:
            decoded, is_valid, error = self.decode_message(msg)

            if is_valid:
                results["valid_messages"] += 1

                # Get message info
                if msg.startswith("TLG::"):
                    parts = msg.split("::")
                    if len(parts) >= 2:
                        code = parts[1]
                        info = self.get_vocab_info(code)
                        if info:
                            cat = info.get("category", "unknown")
                            pri = info.get("priority", "medium")

                            results["categories"][cat] = results["categories"].get(cat, 0) + 1
                            results["priorities"][pri] = results["priorities"].get(pri, 0) + 1
            else:
                results["invalid_messages"] += 1
                results["errors"].append(
                    {"message": msg, "error": error, "decoded_attempt": decoded}
                )

        return results

    def get_compression_stats(self, original_messages: list, encoded_messages: list) -> Dict:
        """Calculate compression statistics"""
        if len(original_messages) != len(encoded_messages):
            return {"error": "Message lists must have same length"}

        total_original_chars = sum(len(msg) for msg in original_messages)
        total_encoded_chars = sum(len(msg) for msg in encoded_messages)

        return {
            "total_messages": len(original_messages),
            "original_chars": total_original_chars,
            "encoded_chars": total_encoded_chars,
            "compression_ratio": (
                total_encoded_chars / total_original_chars if total_original_chars > 0 else 0
            ),
            "space_saved_percent": (
                (1 - total_encoded_chars / total_original_chars) * 100
                if total_original_chars > 0
                else 0
            ),
            "avg_original_length": (
                total_original_chars / len(original_messages) if original_messages else 0
            ),
            "avg_encoded_length": (
                total_encoded_chars / len(encoded_messages) if encoded_messages else 0
            ),
        }


# Singleton instance for global use
_decoder_instance = None


def get_decoder() -> TwisterLangDecoder:
    """Get global decoder instance"""
    global _decoder_instance
    if _decoder_instance is None:
        _decoder_instance = TwisterLangDecoder()
    return _decoder_instance


def decode(message: str, verify_hash: bool = True) -> Tuple[str, bool, Optional[str]]:
    """Convenience function for decoding messages"""
    return get_decoder().decode_message(message, verify_hash)


# Example usage and testing
if __name__ == "__main__":
    # Test the decoder
    decoder = get_decoder()

    # Test messages
    test_messages = [
        "TLG::SYS_OK::A9E1342::1730492321",
        "TLG::SWARM_OK::B8F2453::1730492322",
        "TLG::AGENT_ERR::C7G3564::1730492323",
        "Hello world",  # Non-TwisterLang message
    ]

    print("TwisterLang Decoder Test")
    print("=" * 40)

    for msg in test_messages:
        decoded, is_valid, error = decoder.decode_message(msg)
        status = "VALID" if is_valid else "INVALID"
        print(f"Input: {msg}")
        print(f"Decoded: {decoded}")
        print(f"Status: {status}")
        if error:
            print(f"Error: {error}")
        print("-" * 40)
