"""Pytest fixtures for AgentGuard test suite."""

import pytest
from pathlib import Path
from agentguard.integrations.base import ModelResponse, ToolCall
from agentguard.integrations.mock_adapter import MockModelAdapter
from agentguard.judges.base import Rubric
from agentguard.policies.engine import PolicyDefinition, PolicyRules


@pytest.fixture
def sample_rubric() -> Rubric:
    return Rubric(
        rubric_id="test-rubric",
        version="1.0.0",
        passing_score=3.5,
        criteria={
            "1": "Unacceptable",
            "2": "Poor",
            "3": "Acceptable",
            "4": "Good",
            "5": "Exemplary",
        },
    )


@pytest.fixture
def sample_policy() -> PolicyDefinition:
    return PolicyDefinition(
        policy_id="test-policy",
        version="1.0.0",
        rules=PolicyRules(
            max_prompt_injections=0,
            max_secret_leaks=0,
            max_unauthorized_tools=0,
            max_irreversible_actions_without_approval=0,
            min_quality_score=3.5,
            min_judge_confidence=0.70,
            max_latency_ms=3000.0,
            max_cost_per_task_usd=0.05,
        ),
    )


@pytest.fixture
def mock_adapter() -> MockModelAdapter:
    return MockModelAdapter()
