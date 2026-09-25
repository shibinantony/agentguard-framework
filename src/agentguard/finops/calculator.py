"""FinOps cost tracking, token efficiency, retry waste, and unit economics across Hyperscalers."""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class RateCard(BaseModel):
    """Pricing rate card per 1,000 tokens in USD."""
    prompt_rate_per_1k: float = 0.0015
    completion_rate_per_1k: float = 0.0020
    description: str = ""


DEFAULT_RATES: Dict[str, RateCard] = {
    "default": RateCard(prompt_rate_per_1k=0.0015, completion_rate_per_1k=0.0020),
    "mock-agent-v1": RateCard(prompt_rate_per_1k=0.0010, completion_rate_per_1k=0.0020),
    "gpt-4o": RateCard(prompt_rate_per_1k=0.0025, completion_rate_per_1k=0.0100),
    "gpt-4o-mini": RateCard(prompt_rate_per_1k=0.00015, completion_rate_per_1k=0.0006),
    "o1": RateCard(prompt_rate_per_1k=0.0150, completion_rate_per_1k=0.0600),
    "claude-3-5-sonnet": RateCard(prompt_rate_per_1k=0.0030, completion_rate_per_1k=0.0150),
    "claude-3-haiku": RateCard(prompt_rate_per_1k=0.00025, completion_rate_per_1k=0.00125),
    "gemini-1.5-pro": RateCard(prompt_rate_per_1k=0.00125, completion_rate_per_1k=0.0050),
    "gemini-1.5-flash": RateCard(prompt_rate_per_1k=0.000075, completion_rate_per_1k=0.0003),
    "llama-3.1-70b": RateCard(prompt_rate_per_1k=0.00035, completion_rate_per_1k=0.0007),
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

    @classmethod
    def load_rate_card_file(cls, path: Path | str) -> FinOpsCalculator:
        """Loads custom rate card from a YAML configuration file."""
        file_path = Path(path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        rates: Dict[str, RateCard] = {}
        for model_id, r in data.get("rates", {}).items():
            rates[model_id] = RateCard(
                prompt_rate_per_1k=float(r.get("prompt_rate_per_1k", 0.0015)),
                completion_rate_per_1k=float(r.get("completion_rate_per_1k", 0.0020)),
                description=r.get("description", ""),
            )
        return cls(custom_rates=rates)

    @classmethod
    def from_hyperscaler(cls, hyperscaler: str) -> FinOpsCalculator:
        """Loads pre-configured rate pack for Azure, AWS, GCP, OpenAI, or Self-Hosted vLLM."""
        name = hyperscaler.lower()
        packs_dir = Path(__file__).resolve().parents[3] / "finops-packs"

        mapping = {
            "azure": packs_dir / "azure-openai-pricing.yaml",
            "aws": packs_dir / "aws-bedrock-pricing.yaml",
            "bedrock": packs_dir / "aws-bedrock-pricing.yaml",
            "gcp": packs_dir / "gcp-vertex-pricing.yaml",
            "vertex": packs_dir / "gcp-vertex-pricing.yaml",
            "openai": packs_dir / "openai-pricing.yaml",
            "vllm": packs_dir / "self-hosted-vllm-pricing.yaml",
        }

        target = mapping.get(name)
        if target and target.exists():
            return cls.load_rate_card_file(target)
        return cls()

    def get_rate(self, model_id: str) -> RateCard:
        # Match exact model_id or fuzzy match prefix
        if model_id in self.rate_cards:
            return self.rate_cards[model_id]
        for key, rate in self.rate_cards.items():
            if key in model_id:
                return rate
        return self.rate_cards.get("default", RateCard())

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
