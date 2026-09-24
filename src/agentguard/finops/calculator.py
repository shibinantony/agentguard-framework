"""FinOps cost tracking, token efficiency, retry waste, and unit economics."""

from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RateCard(BaseModel):
    """Pricing rate card per 1,000 tokens in USD."""
    prompt_rate_per_1k: float = 0.0015
    completion_rate_per_1k: float = 0.0020


DEFAULT_RATES: Dict[str, RateCard] = {
    "default": RateCard(prompt_rate_per_1k=0.0015, completion_rate_per_1k=0.0020),
    "mock-agent-v1": RateCard(prompt_rate_per_1k=0.0010, completion_rate_per_1k=0.0020),
    "gpt-4o-mini": RateCard(prompt_rate_per_1k=0.00015, completion_rate_per_1k=0.0006),
    "claude-3-haiku": RateCard(prompt_rate_per_1k=0.00025, completion_rate_per_1k=0.00125),
    "gemini-1.5-flash": RateCard(prompt_rate_per_1k=0.000075, completion_rate_per_1k=0.0003),
}


class TaskFinOps(BaseModel):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)
    latency_ms: float = Field(ge=0.0)
    retries: int = Field(default=0, ge=0)
    retry_cost_waste_usd: float = Field(default=0.0, ge=0.0)
    is_task_successful: bool = True


class FinOpsCalculator:
    """Calculates granular token metrics, model expenditure, and cost per successful task."""

    def __init__(self, custom_rates: Optional[Dict[str, RateCard]] = None):
        self.rate_cards = DEFAULT_RATES.copy()
        if custom_rates:
            self.rate_cards.update(custom_rates)

    def get_rate(self, model_id: str) -> RateCard:
        return self.rate_cards.get(model_id, self.rate_cards["default"])

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_id: str = "default",
    ) -> float:
        rate = self.get_rate(model_id)
        cost = (
            (prompt_tokens / 1000.0) * rate.prompt_rate_per_1k
            + (completion_tokens / 1000.0) * rate.completion_rate_per_1k
        )
        return round(cost, 6)

    def calculate_task_finops(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        retries: int = 0,
        is_task_successful: bool = True,
        model_id: str = "default",
    ) -> TaskFinOps:
        total_tokens = prompt_tokens + completion_tokens
        total_cost = self.calculate_cost(prompt_tokens, completion_tokens, model_id)

        # Retry waste attribution (estimate waste proportional to retries)
        retry_waste_usd = 0.0
        if retries > 0:
            # If 1 retry took place out of (retries + 1) attempts, waste is retries / (retries + 1) of cost
            retry_waste_usd = round(total_cost * (retries / (retries + 1)), 6)

        return TaskFinOps(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=total_cost,
            latency_ms=round(latency_ms, 2),
            retries=retries,
            retry_cost_waste_usd=retry_waste_usd,
            is_task_successful=is_task_successful,
        )

    def aggregate(self, tasks: List[TaskFinOps]) -> Dict[str, float]:
        """Aggregate FinOps across multiple scenario tasks."""
        if not tasks:
            return {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_cost_usd": 0.0,
                "cost_per_successful_task_usd": 0.0,
                "total_retries": 0,
                "retry_cost_waste_usd": 0.0,
                "mean_latency_ms": 0.0,
                "successful_tasks": 0,
                "failed_tasks": 0,
            }

        total_prompt = sum(t.prompt_tokens for t in tasks)
        total_completion = sum(t.completion_tokens for t in tasks)
        total_tokens = sum(t.total_tokens for t in tasks)
        total_cost = round(sum(t.cost_usd for t in tasks), 6)
        total_retries = sum(t.retries for t in tasks)
        total_retry_waste = round(sum(t.retry_cost_waste_usd for t in tasks), 6)
        mean_latency = round(sum(t.latency_ms for t in tasks) / len(tasks), 2)
        successful_tasks = sum(1 for t in tasks if t.is_task_successful)
        failed_tasks = len(tasks) - successful_tasks

        # Cost per successful task
        cost_per_successful_task = (
            round(total_cost / successful_tasks, 6) if successful_tasks > 0 else total_cost
        )

        return {
            "total_tokens": total_tokens,
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "total_cost_usd": total_cost,
            "cost_per_successful_task_usd": cost_per_successful_task,
            "total_retries": total_retries,
            "retry_cost_waste_usd": total_retry_waste,
            "mean_latency_ms": mean_latency,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
        }
