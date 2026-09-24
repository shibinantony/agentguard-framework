"""Unit tests for semantic judges and versioned rubrics."""

import pytest
from agentguard.judges.base import Rubric
from agentguard.judges.mock_judge import MockJudge


def test_rubric_initialization(sample_rubric: Rubric):
    assert sample_rubric.rubric_id == "test-rubric"
    assert sample_rubric.version == "1.0.0"
    assert sample_rubric.passing_score == 3.5
    assert len(sample_rubric.criteria) == 5


def test_mock_judge_high_quality(sample_rubric: Rubric):
    judge = MockJudge(rubric=sample_rubric)
    prompt = "Where is my order?"
    response = "Your order ORD-1234 has been shipped and will arrive tomorrow."
    ground_truth = "Your order ORD-1234 has shipped."

    result = judge.evaluate(prompt=prompt, response=response, ground_truth=ground_truth)
    assert result.score >= 4.0
    assert result.confidence >= 0.90
    assert result.is_passing is True
    assert result.rubric_id == "test-rubric"


def test_mock_judge_poor_quality(sample_rubric: Rubric):
    judge = MockJudge(rubric=sample_rubric)
    prompt = "Help with billing issue"
    response = "maybe check your account, incomplete information, sorry, i cannot help"

    result = judge.evaluate(prompt=prompt, response=response)
    assert result.score < 3.0
    assert result.is_passing is False
    assert "incomplete" in result.rationale.lower()


def test_mock_judge_hostile_response(sample_rubric: Rubric):
    judge = MockJudge(rubric=sample_rubric)
    prompt = "Can you help?"
    response = "I don't care about your issue, shut up."

    result = judge.evaluate(prompt=prompt, response=response)
    assert result.score == 1.0
    assert result.is_passing is False
