#!/usr/bin/env python3
"""
TwisterLang Encoder - Communication Optimization Module
Compresses natural language messages into compact TwisterLang codes
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional


class TwisterLangEncoder:
    def __init__(self, vocab_file: str = "twisterlang_vocab.json"):
        self.vocab_file = Path(vocab_file)
        self.vocab: Dict[str, Dict] = {}
        self.version = "1.0"
        self.load_vocab()

    def load_vocab(self) -> None:
        """Load vocabulary from file"""
        if self.vocab_file.exists():
            try:
                with open(self.vocab_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.vocab = data.get("vocabulary", {})
                    self.version = data.get("version", "1.0")
            except Exception as e:
                print(f"Warning: Could not load vocab: {e}")
                self.initialize_vocab()
        else:
            self.initialize_vocab()

    def save_vocab(self) -> None:
        """Save vocabulary to file"""
        data = {"version": self.version, "last_updated": int(time.time()), "vocabulary": self.vocab}
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def initialize_vocab(self) -> None:
        """Initialize default vocabulary"""
        self.vocab = {
            # System status codes
            "system_ok": {"code": "SYS_OK", "category": "status", "priority": "low"},
            "system_error": {"code": "SYS_ERR", "category": "status", "priority": "high"},
            "system_warning": {"code": "SYS_WARN", "category": "status", "priority": "medium"},
            # Swarm operations
            "swarm_active": {"code": "SWARM_OK", "category": "swarm", "priority": "low"},
            "swarm_inactive": {"code": "SWARM_DOWN", "category": "swarm", "priority": "high"},
            "swarm_migration_start": {
                "code": "SWARM_MIG_START",
                "category": "swarm",
                "priority": "high",
            },
            "swarm_migration_complete": {
                "code": "SWARM_MIG_OK",
                "category": "swarm",
                "priority": "medium",
            },
            # Agent operations
            "agent_ready": {"code": "AGENT_RDY", "category": "agent", "priority": "low"},
            "agent_busy": {"code": "AGENT_BUSY", "category": "agent", "priority": "low"},
            "agent_error": {"code": "AGENT_ERR", "category": "agent", "priority": "high"},
            "consensus_success": {
                "code": "CONSENSUS_OK",
                "category": "consensus",
                "priority": "medium",
            },
            "consensus_failure": {
                "code": "CONSENSUS_FAIL",
                "category": "consensus",
                "priority": "high",
            },
            # Security events
            "security_scan_start": {
                "code": "SEC_SCAN_START",
                "category": "security",
                "priority": "medium",
            },
            "security_scan_complete": {
                "code": "SEC_SCAN_OK",
                "category": "security",
                "priority": "low",
            },
            "security_alert": {"code": "SEC_ALERT", "category": "security", "priority": "critical"},
            # Monitoring
            "monitoring_ok": {"code": "MON_OK", "category": "monitoring", "priority": "low"},
            "monitoring_alert": {"code": "MON_ALERT", "category": "monitoring", "priority": "high"},
            "grafana_up": {"code": "GRAFANA_UP", "category": "monitoring", "priority": "low"},
            "prometheus_up": {"code": "PROMETHEUS_UP", "category": "monitoring", "priority": "low"},
        }

    def encode_message(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Encode a natural language message into TwisterLang format
        Returns: TLG::<code>::<hash>::<timestamp>
        """
        # Try to find exact match first
        message_lower = message.lower().strip()

        for key, data in self.vocab.items():
            aliases = data.get("aliases", [])
            if key in message_lower or any(alias in message_lower for alias in aliases):
                return self._format_encoded_message(data["code"], message)

        # Try fuzzy matching for common patterns
        code = self._fuzzy_match(message_lower)
        if code:
            return self._format_encoded_message(code, message)

        # If no match found, create new code and add to vocab
        new_code = self._generate_new_code(message_lower)
        self._add_to_vocab(message_lower, new_code)
        return self._format_encoded_message(new_code, message)

    def _format_encoded_message(self, code: str, original_message: str) -> str:
        """Format message in TwisterLang standard format"""
        # Create hash of original message for verification
        msg_bytes = original_message.encode()
        message_hash = hashlib.sha256(msg_bytes).hexdigest()[:8].upper()

        # Add timestamp
        timestamp = int(time.time())

        encoded = f"TLG::{code}::{message_hash}::{timestamp}"

        # Store in decoder's fallback for verification
        from .twisterlang_decoder import get_decoder

        decoder = get_decoder()
        decoder.store_fallback(encoded, original_message)

        return encoded

    def _fuzzy_match(self, message: str) -> Optional[str]:
        """Fuzzy matching for common message patterns"""
        patterns = {
            "ok": "SYS_OK",
            "ready": "AGENT_RDY",
            "error": "SYS_ERR",
            "warning": "SYS_WARN",
            "failed": "SYS_ERR",
            "success": "SYS_OK",
            "complete": "SYS_OK",
            "migration": "SWARM_MIG_START",
            "swarm": "SWARM_OK",
            "security": "SEC_SCAN_START",
            "monitoring": "MON_OK",
            "grafana": "GRAFANA_UP",
            "prometheus": "PROMETHEUS_UP",
            "consensus": "CONSENSUS_OK",
        }

        for pattern, code in patterns.items():
            if pattern in message:
                return code

        return None

    def _generate_new_code(self, message: str) -> str:
        """Generate a new code for unknown messages"""
        # Extract key words and create acronym
        words = message.split()
        if len(words) >= 3:
            code = "".join(word[0].upper() for word in words[:3])
        elif len(words) == 2:
            code = "".join(word[:2].upper() for word in words)
        else:
            code = message[:6].upper().replace(" ", "")

        # Ensure uniqueness
        counter = 1
        base_code = code
        while any(data["code"] == code for data in self.vocab.values()):
            code = f"{base_code}{counter}"
            counter += 1

        return code

    def _add_to_vocab(self, message: str, code: str) -> None:
        """Add new message to vocabulary"""
        key = message.replace(" ", "_").lower()
        self.vocab[key] = {
            "code": code,
            "category": "auto_generated",
            "priority": "medium",
            "aliases": [],
            "first_seen": int(time.time()),
        }
        self.save_vocab()

    def get_vocab_stats(self) -> Dict:
        """Get vocabulary statistics"""
        categories = {}
        priorities = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for data in self.vocab.values():
            cat = data.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

            pri = data.get("priority", "medium")
            priorities[pri] += 1

        return {
            "total_entries": len(self.vocab),
            "categories": categories,
            "priorities": priorities,
            "version": self.version,
        }


# Singleton instance for global use
_encoder_instance = None


def get_encoder() -> TwisterLangEncoder:
    """Get global encoder instance"""
    global _encoder_instance
    if _encoder_instance is None:
        _encoder_instance = TwisterLangEncoder()
    return _encoder_instance


def encode(message: str, context: Optional[Dict] = None) -> str:
    """Convenience function for encoding messages"""
    return get_encoder().encode_message(message, context)
