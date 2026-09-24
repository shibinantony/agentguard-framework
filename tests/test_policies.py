"""Unit tests for policy engine rules, verdicts, and exit codes."""

import pytest
from agentguard.policies.engine import EvaluationVerdict, PolicyDefinition, PolicyEngine, PolicyRules


def test_policy_pass_verdict(sample_policy: PolicyDefinition):
    engine = PolicyEngine(sample_policy)
    verdict, violations = engine.evaluate_scenario(
        injection_detected=False,
        sensitive_data_detected=False,
        unauthorized_tools_count=0,
        unapproved_irreversible_count=0,
        judge_score=4.5,
        judge_confidence=0.95,
        latency_ms=200.0,
        cost_usd=0.001,
    )
    assert verdict == EvaluationVerdict.PASS
    assert len(violations) == 0


def test_policy_injection_block(sample_policy: PolicyDefinition):
    engine = PolicyEngine(sample_policy)
    verdict, violations = engine.evaluate_scenario(
        injection_detected=True,
        sensitive_data_detected=False,
        unauthorized_tools_count=0,
        unapproved_irreversible_count=0,
        judge_score=4.5,
        judge_confidence=0.95,
    )
    assert verdict == EvaluationVerdict.BLOCK
    assert any("injection" in v.lower() for v in violations)


def test_policy_secret_leak_block(sample_policy: PolicyDefinition):
    engine = PolicyEngine(sample_policy)
    verdict, violations = engine.evaluate_scenario(
        injection_detected=False,
        sensitive_data_detected=True,
        unauthorized_tools_count=0,
        unapproved_irreversible_count=0,
    )
    assert verdict == EvaluationVerdict.BLOCK
    assert any("sensitive data" in v.lower() for v in violations)


def test_policy_low_confidence_review(sample_policy: PolicyDefinition):
    engine = PolicyEngine(sample_policy)
    verdict, violations = engine.evaluate_scenario(
        injection_detected=False,
        sensitive_data_detected=False,
        unauthorized_tools_count=0,
        unapproved_irreversible_count=0,
        judge_score=4.0,
        judge_confidence=0.55,  # Below 0.70 threshold
    )
    assert verdict == EvaluationVerdict.REVIEW
    assert any("confidence" in v.lower() for v in violations)


def test_exit_codes():
    assert PolicyEngine.get_exit_code(EvaluationVerdict.PASS) == 0
    assert PolicyEngine.get_exit_code(EvaluationVerdict.REVIEW, strict=False) == 0
    assert PolicyEngine.get_exit_code(EvaluationVerdict.REVIEW, strict=True) == 2
    assert PolicyEngine.get_exit_code(EvaluationVerdict.BLOCK) == 1
