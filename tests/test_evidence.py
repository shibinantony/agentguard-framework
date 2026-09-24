"""Unit tests for evidence receipt creation, canonical hashing, and HTML reporting."""

from pathlib import Path
import pytest
from agentguard.evidence.receipt import EvidenceGenerator, compute_canonical_hash
from agentguard.evidence.html_report import HTMLReportRenderer


def test_canonical_hash_consistency():
    d1 = {"b": 2, "a": 1, "c": [3, 4]}
    d2 = {"a": 1, "c": [3, 4], "b": 2}
    # Deterministic regardless of dict insertion order
    assert compute_canonical_hash(d1) == compute_canonical_hash(d2)


def test_evidence_receipt_creation_and_verification(tmp_path: Path):
    gen = EvidenceGenerator()
    summary = {
        "total_scenarios": 1,
        "passed_scenarios": 1,
        "failed_scenarios": 0,
        "mean_quality_score": 4.5,
        "total_tokens": 100,
        "prompt_tokens": 60,
        "completion_tokens": 40,
        "total_cost_usd": 0.0001,
        "cost_per_successful_task_usd": 0.0001,
        "total_retries": 0,
        "mean_latency_ms": 120.0,
    }
    scenarios = [
        {
            "scenario_id": "test-1",
            "name": "Test Scenario",
            "verdict": "PASS",
            "safety_checks": {
                "injection_detected": False,
                "sensitive_data_detected": False,
                "unauthorized_tools": [],
            },
            "judge_evaluation": {
                "rubric_id": "rubric-1",
                "rubric_version": "1.0",
                "score": 4.5,
                "confidence": 0.95,
                "rationale": "High quality answer.",
            },
            "finops": {
                "prompt_tokens": 60,
                "completion_tokens": 40,
                "total_tokens": 100,
                "cost_usd": 0.0001,
                "latency_ms": 120.0,
                "retries": 0,
                "is_task_successful": True,
            },
        }
    ]

    receipt = gen.create_receipt(
        receipt_id="rcpt-test-123",
        timestamp="2026-09-24T18:00:00Z",
        framework_version="0.1.0",
        agent_id="test-agent",
        policy_id="test-policy",
        verdict="PASS",
        summary=summary,
        scenarios=scenarios,
    )

    assert "integrity" in receipt
    assert receipt["integrity"]["algorithm"] == "SHA-256"
    assert len(receipt["integrity"]["canonical_hash"]) == 64

    # Verify signature
    assert gen.verify_receipt(receipt) is True

    # Tampering test
    tampered = receipt.copy()
    tampered["verdict"] = "BLOCK"
    assert gen.verify_receipt(tampered) is False

    # Save to disk
    json_file = tmp_path / "evidence.json"
    gen.save_receipt(receipt, json_file)
    assert json_file.exists()


def test_html_report_rendering(tmp_path: Path):
    renderer = HTMLReportRenderer()
    sample_receipt = {
        "receipt_id": "rcpt-123",
        "agent_id": "agent-test",
        "policy_id": "policy-test",
        "framework_version": "0.1.0",
        "timestamp": "2026-09-24T18:00:00Z",
        "verdict": "PASS",
        "summary": {
            "total_scenarios": 1,
            "passed_scenarios": 1,
            "failed_scenarios": 0,
            "mean_quality_score": 4.5,
            "total_tokens": 80,
            "total_cost_usd": 0.0002,
            "cost_per_successful_task_usd": 0.0002,
            "mean_latency_ms": 150.0,
        },
        "scenarios": [],
        "integrity": {
            "algorithm": "SHA-256",
            "canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        },
    }

    html = renderer.render(sample_receipt)
    assert "<!DOCTYPE html>" in html
    assert "agent-test" in html
    assert "SHA-256" in html

    html_file = tmp_path / "report.html"
    renderer.save_report(sample_receipt, html_file)
    assert html_file.exists()
