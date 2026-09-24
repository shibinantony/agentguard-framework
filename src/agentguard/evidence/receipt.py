"""Cryptographic Evidence Receipt Generator with SHA-256 integrity and schema validation."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import jsonschema


def compute_canonical_hash(payload: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 hash over canonical JSON representation."""
    canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class EvidenceGenerator:
    """Generates structured JSON evidence receipts compliant with evidence-receipt.schema.json."""

    def __init__(self, schema_path: Optional[Path] = None):
        if schema_path is None:
            schema_path = Path(__file__).resolve().parents[3] / "schemas" / "evidence-receipt.schema.json"
        self.schema_path = schema_path
        self._schema = None
        if self.schema_path.exists():
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)

    def create_receipt(
        self,
        receipt_id: str,
        timestamp: str,
        framework_version: str,
        agent_id: str,
        policy_id: str,
        verdict: str,
        summary: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assembles and signs evidence receipt with SHA-256 canonical checksum."""
        # 1. Base payload for canonical hashing
        body = {
            "receipt_id": receipt_id,
            "timestamp": timestamp,
            "framework_version": framework_version,
            "agent_id": agent_id,
            "policy_id": policy_id,
            "verdict": verdict,
            "summary": summary,
            "scenarios": scenarios,
        }

        canonical_hash = compute_canonical_hash(body)

        receipt = {
            **body,
            "integrity": {
                "algorithm": "SHA-256",
                "canonical_hash": canonical_hash,
            },
        }

        # 2. Validate against schema if available
        if self._schema:
            jsonschema.validate(instance=receipt, schema=self._schema)

        return receipt

    def save_receipt(self, receipt: Dict[str, Any], output_path: Path) -> Path:
        """Saves formatted receipt to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)
        return output_path

    @staticmethod
    def verify_receipt(receipt: Dict[str, Any]) -> bool:
        """Verifies that the canonical SHA-256 hash in receipt matches its contents."""
        integrity = receipt.get("integrity", {})
        claimed_hash = integrity.get("canonical_hash")
        if not claimed_hash:
            return False

        # Build payload without integrity block
        body = {k: v for k, v in receipt.items() if k != "integrity"}
        expected_hash = compute_canonical_hash(body)
        return expected_hash == claimed_hash
