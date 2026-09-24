"""Unit tests for FinOps calculator, rate cards, retry waste, and cost per successful task."""

import pytest
from agentguard.finops.calculator import FinOpsCalculator, RateCard, TaskFinOps


def test_finops_calculation():
    calc = FinOpsCalculator()
    # 1000 prompt tokens @ $0.0015 = 0.0015
    # 500 completion tokens @ $0.0020 = 0.0010
    # Total = 0.0025
    cost = calc.calculate_cost(prompt_tokens=1000, completion_tokens=500, model_id="default")
    assert cost == 0.0025


def test_task_finops_with_retry_waste():
    calc = FinOpsCalculator()
    # 1 retry performed
    task = calc.calculate_task_finops(
        prompt_tokens=1000,
        completion_tokens=1000,
        latency_ms=250.0,
        retries=1,
        is_task_successful=True,
    )
    assert task.total_tokens == 2000
    assert task.cost_usd > 0
    assert task.retry_cost_waste_usd > 0
    # With 1 retry, retry waste is 1/2 of total cost
    assert round(task.retry_cost_waste_usd, 4) == round(task.cost_usd / 2, 4)


def test_finops_aggregate_cost_per_successful_task():
    calc = FinOpsCalculator()
    tasks = [
        TaskFinOps(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.01, latency_ms=100, retries=0, is_task_successful=True),
        TaskFinOps(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.01, latency_ms=100, retries=0, is_task_successful=True),
        TaskFinOps(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.01, latency_ms=100, retries=0, is_task_successful=False),
    ]

    agg = calc.aggregate(tasks)
    assert agg["total_tokens"] == 450
    assert agg["total_cost_usd"] == 0.03
    assert agg["successful_tasks"] == 2
    assert agg["failed_tasks"] == 1
    # Cost per successful task = $0.03 / 2 = $0.015
    assert agg["cost_per_successful_task_usd"] == 0.015
