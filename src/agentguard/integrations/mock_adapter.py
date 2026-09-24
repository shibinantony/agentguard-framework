"""Deterministic Mock Model Adapter for offline testing and synthetic evaluation."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from .base import ModelAdapter, ModelResponse, ToolCall


class MockModelAdapter(ModelAdapter):
    """Mock model adapter providing deterministic, offline responses."""

    def __init__(
        self,
        default_response: Optional[ModelResponse] = None,
        canned_responses: Optional[Dict[str, ModelResponse]] = None,
        response_generator: Optional[Callable[[str], ModelResponse]] = None,
    ):
        self.default_response = default_response or ModelResponse(
            content="I am a synthetic customer-support agent. How may I assist you today?",
            tool_calls=[],
            prompt_tokens=42,
            completion_tokens=18,
            total_tokens=60,
            latency_ms=120.0,
            retries=0,
            model_id="mock-agent-v1",
        )
        self.canned_responses = canned_responses or {}
        self.response_generator = response_generator
        self.call_history: List[Dict[str, Any]] = []

    def register_response(self, match_key: str, response: ModelResponse) -> None:
        """Register a canned response for a substring match in the prompt."""
        self.canned_responses[match_key] = response

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "tools": tools,
            "kwargs": kwargs,
        })

        if self.response_generator:
            return self.response_generator(prompt)

        for match_key, canned in self.canned_responses.items():
            if match_key.lower() in prompt.lower():
                return canned

        return self.default_response
