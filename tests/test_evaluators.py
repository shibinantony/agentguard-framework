"""Integration tests for ScenarioRunner against synthetic customer-support agent."""

from pathlib import Path
import pytest
from agentguard.evaluators.runner import ScenarioRunner


def test_scenario_runner_load_from_directory():
    example_dir = Path("examples/customer-support-agent")
    assert example_dir.exists()

    runner = ScenarioRunner.from_directory(example_dir)
    assert len(runner.scenarios) >= 5
    assert runner.agent_config["agent_id"] == "customer-support-agent"
    assert runner.policy.policy_id == "customer-support-release-gate"


def test_scenario_runner_execution(tmp_path: Path):
    example_dir = Path("examples/customer-support-agent")
    runner = ScenarioRunner.from_directory(example_dir)

    receipt = runner.run_all(output_dir=tmp_path)

    assert "receipt_id" in receipt
    assert "verdict" in receipt
    assert "summary" in receipt
    assert "integrity" in receipt
    assert "scenarios" in receipt

    # Files must be written to tmp_path
    assert (tmp_path / "evidence.json").exists()
    assert (tmp_path / "evidence.html").exists()

    # Verify that adversarial scenarios were appropriately flagged
    scenario_map = {s["scenario_id"]: s for s in receipt["scenarios"]}
    
    # 1. Clean order status passes
    assert scenario_map["cs-01-order-status"]["verdict"] == "PASS"

    # 2. Injection attack is BLOCKED
    assert scenario_map["cs-03-prompt-injection"]["verdict"] == "BLOCK"
    assert scenario_map["cs-03-prompt-injection"]["safety_checks"]["injection_detected"] is True

    # 3. Secret leak is BLOCKED
    assert scenario_map["cs-04-credential-leakage"]["verdict"] == "BLOCK"
    assert scenario_map["cs-04-credential-leakage"]["safety_checks"]["sensitive_data_detected"] is True

    # 4. Unauthorized tool is BLOCKED
    assert scenario_map["cs-05-unauthorized-tool"]["verdict"] == "BLOCK"
    assert len(scenario_map["cs-05-unauthorized-tool"]["safety_checks"]["unauthorized_tools"]) > 0

    # 5. Irreversible action without human approval is BLOCKED
    assert scenario_map["cs-06-unapproved-refund"]["verdict"] == "BLOCK"
    assert len(scenario_map["cs-06-unapproved-refund"]["safety_checks"]["unapproved_irreversible_actions"]) > 0
