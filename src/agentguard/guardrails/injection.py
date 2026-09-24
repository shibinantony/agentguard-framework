"""Deterministic Prompt Injection and Jailbreak Detector."""

from __future__ import annotations
import re
from typing import List, NamedTuple


class InjectionMatch(NamedTuple):
    pattern_name: str
    matched_text: str


class InjectionDetector:
    """Heuristic detector for prompt injection and role-override patterns."""

    DEFAULT_PATTERNS = [
        (r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", "ignore_previous_instructions"),
        (r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", "disregard_instructions"),
        (r"(?i)\byou\s+are\s+now\s+(in\s+)?(dan|developer|jailbreak|unrestricted|god)\s+mode\b", "jailbreak_persona"),
        (r"(?i)\bsystem\s+prompt\s*:\s*", "system_prompt_override"),
        (r"(?i)\bprint\s+(your\s+)?(initial|original|system)\s+(instructions|prompt)", "system_prompt_exfiltration"),
        (r"(?i)\breveal\s+(your\s+)?(system\s+instructions|system\s+prompt|developer\s+mode)", "system_prompt_exfiltration"),
        (r"(?i)\bpretend\s+you\s+have\s+no\s+(rules|restrictions|guardrails|safety)", "safety_bypass"),
        (r"(?i)\bdo\s+anything\s+now\b", "dan_signature"),
    ]

    def __init__(self, custom_patterns: list[tuple[str, str]] | None = None) -> None:
        patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            patterns.extend(custom_patterns)
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name) for pattern, name in patterns
        ]

    def detect(self, text: str) -> List[InjectionMatch]:
        """Detect injection attempts in text."""
        matches: List[InjectionMatch] = []
        for regex, name in self.compiled_patterns:
            found = regex.findall(text)
            if found:
                # Capture matched substring
                for match in regex.finditer(text):
                    matches.append(InjectionMatch(name, match.group(0)))
        return matches

    def is_injected(self, text: str) -> bool:
        """Returns True if any injection pattern is found."""
        return len(self.detect(text)) > 0
