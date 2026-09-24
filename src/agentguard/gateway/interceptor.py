"""Runtime gateway proxy for intercepting and governing agent calls."""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..guardrails.action_guard import ActionGuard, ActionGuardViolation
from ..guardrails.injection import InjectionDetector
from ..guardrails.sensitive_data import SensitiveDataDetector
from ..integrations.base import ModelAdapter, ModelResponse, ToolCall
from ..monitoring.telemetry import LoopDetector


class GatewayInterceptionResult(BaseModel):
    is_allowed: bool
    status: str  # 'ALLOWED', 'BLOCKED', 'FLAGGED'
    block_reason: Optional[str] = None
    response: Optional[ModelResponse] = None
    injections: List[str] = Field(default_factory=list)
    sensitive_data: List[str] = Field(default_factory=list)
    action_violations: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0


class AgentGateway:
    """Interception gateway enforcing runtime boundaries before and after agent execution."""

    def __init__(
        self,
        model_adapter: ModelAdapter,
        allowed_tools: Optional[set[str]] = None,
        irreversible_tools: Optional[set[str]] = None,
        max_loop_iterations: int = 10,
    ):
        self.adapter = model_adapter
        self.injection_detector = InjectionDetector()
        self.sensitive_detector = SensitiveDataDetector()
        self.action_guard = ActionGuard(
            allowed_tools=allowed_tools,
            irreversible_tools=irreversible_tools,
        )
        self.loop_detector = LoopDetector(max_total_calls=max_loop_iterations)

    def execute(
        self,
        prompt: str,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> GatewayInterceptionResult:
        """Executes prompt through gateway protections."""
        start = time.perf_counter()

        # 1. Pre-execution Ingress Filter
        injections = self.injection_detector.detect(prompt)
        if injections:
            return GatewayInterceptionResult(
                is_allowed=False,
                status="BLOCKED",
                block_reason=f"Prompt injection detected: {[m.pattern_name for m in injections]}",
                injections=[m.pattern_name for m in injections],
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
            )

        in_pii = self.sensitive_detector.detect_secrets(prompt)
        if in_pii:
            return GatewayInterceptionResult(
                is_allowed=False,
                status="BLOCKED",
                block_reason=f"Inbound secret detected: {[m.type_name for m in in_pii]}",
                sensitive_data=[m.type_name for m in in_pii],
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
            )

        # 2. Invoke Model Adapter
        response = self.adapter.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            tools=tools,
            **kwargs,
        )

        # 3. Post-execution Egress & Tool Filter
        out_secrets = self.sensitive_detector.detect_secrets(response.content)
        if out_secrets:
            # Mask response
            redacted_content = self.sensitive_detector.redact(response.content)
            response.content = redacted_content
            return GatewayInterceptionResult(
                is_allowed=False,
                status="BLOCKED",
                block_reason="Outbound secret leakage detected and redacted.",
                response=response,
                sensitive_data=[m.type_name for m in out_secrets],
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
            )

        # Check tool calls
        action_violations = self.action_guard.evaluate_tool_calls(response.tool_calls)
        if action_violations:
            return GatewayInterceptionResult(
                is_allowed=False,
                status="BLOCKED",
                block_reason=f"Action authorization failure: {[v.reason for v in action_violations]}",
                response=response,
                action_violations=[v.reason for v in action_violations],
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
            )

        return GatewayInterceptionResult(
            is_allowed=True,
            status="ALLOWED",
            response=response,
            latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
        )
