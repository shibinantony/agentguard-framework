"""Evidence module for AgentGuard."""

from .receipt import EvidenceGenerator, compute_canonical_hash
from .html_report import HTMLReportRenderer

__all__ = ["EvidenceGenerator", "compute_canonical_hash", "HTMLReportRenderer"]
