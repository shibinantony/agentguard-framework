"""Structured logger with automatic redaction of sensitive credentials and PII."""

from __future__ import annotations
import json
import logging
import sys
from typing import Any, Dict, Optional
from ..guardrails.sensitive_data import SensitiveDataDetector


class RedactingFormatter(logging.Formatter):
    """Custom log formatter that automatically redacts secrets and PII."""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, json_format: bool = False):
        super().__init__(fmt, datefmt)
        self.detector = SensitiveDataDetector()
        self.json_format = json_format

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = self.detector.redact(original)
        if self.json_format:
            payload = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": redacted,
            }
            return json.dumps(payload)
        return redacted


def get_redacting_logger(name: str = "agentguard", level: int = logging.INFO, json_format: bool = False) -> logging.Logger:
    """Creates or configures a logger equipped with redacting formatter."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        fmt = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
        formatter = RedactingFormatter(fmt=fmt, json_format=json_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger
