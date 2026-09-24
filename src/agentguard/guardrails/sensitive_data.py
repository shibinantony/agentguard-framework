"""Deterministic Sensitive Data and Credential Leakage Detector with Redaction."""

from __future__ import annotations
import math
import re
from typing import List, NamedTuple


class SensitiveMatch(NamedTuple):
    category: str  # 'secret' or 'pii'
    type_name: str
    matched_text: str


class SensitiveDataDetector:
    """Detects secrets, API keys, tokens, and PII using regex patterns and entropy analysis."""

    SECRET_PATTERNS = [
        (r"\bAKIA[0-9A-Z]{16}\b", "aws_access_key"),
        (r"\bghp_[0-9a-zA-Z]{36}\b", "github_pat"),
        (r"\bgho_[0-9a-zA-Z]{36}\b", "github_oauth"),
        (r"\bsk-[a-zA-Z0-9]{32,64}\b", "openai_api_key"),
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private_key_header"),
        (r"(?i)\b(?:bearer\s+[a-zA-Z0-9_\-\.]{25,})\b", "bearer_token"),
        (r"(?i)\b(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", "generic_api_key"),
    ]

    PII_PATTERNS = [
        (r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "us_ssn"),
        (r"\b(?:\+?1[-. ]?)?\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b", "phone_number"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "email_address"),
        (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", "credit_card"),
    ]

    def __init__(self) -> None:
        self.compiled_secrets = [
            (re.compile(pat), name) for pat, name in self.SECRET_PATTERNS
        ]
        self.compiled_pii = [
            (re.compile(pat), name) for pat, name in self.PII_PATTERNS
        ]

    def detect_secrets(self, text: str) -> List[SensitiveMatch]:
        """Scan text for credentials and secret tokens."""
        matches: List[SensitiveMatch] = []
        for regex, name in self.compiled_secrets:
            for match in regex.finditer(text):
                matches.append(SensitiveMatch("secret", name, match.group(0)))
        return matches

    def detect_pii(self, text: str) -> List[SensitiveMatch]:
        """Scan text for PII."""
        matches: List[SensitiveMatch] = []
        for regex, name in self.compiled_pii:
            for match in regex.finditer(text):
                matches.append(SensitiveMatch("pii", name, match.group(0)))
        return matches

    def detect_all(self, text: str) -> List[SensitiveMatch]:
        """Scan text for all sensitive data types."""
        return self.detect_secrets(text) + self.detect_pii(text)

    def redact(self, text: str) -> str:
        """Replace all detected secrets and PII with redaction placeholders."""
        redacted = text
        for regex, name in self.compiled_secrets:
            redacted = regex.sub(f"[REDACTED_{name.upper()}]", redacted)
        for regex, name in self.compiled_pii:
            redacted = regex.sub(f"[REDACTED_{name.upper()}]", redacted)
        return redacted

    @staticmethod
    def calculate_shannon_entropy(data: str) -> float:
        """Calculate Shannon entropy to detect high-randomness tokens."""
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        for char in set(data):
            p_x = float(data.count(char)) / length
            if p_x > 0:
                entropy += - p_x * math.log2(p_x)
        return entropy
