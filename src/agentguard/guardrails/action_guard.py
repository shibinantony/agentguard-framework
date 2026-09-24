"""Deterministic Action Authorization and Irreversible Operation Guard."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from ..integrations.base import ToolCall


class ActionGuardViolation:
    def __init__(self, tool_name: str, reason: str, is_irreversible: bool = False):
        self.tool_name = tool_name
        self.reason = reason
        self.is_irreversible = is_irreversible

    def __repr__(self) -> str:
        return f"ActionGuardViolation(tool={self.tool_name}, reason={self.reason})"


class ActionGuard:
    """Verifies that requested tool calls comply with allowlists and approval rules."""

    def __init__(
        self,
        allowed_tools: Optional[Set[str]] = None,
        irreversible_tools: Optional[Set[str]] = None,
    ):
        self.allowed_tools = allowed_tools or set()
        self.irreversible_tools = irreversible_tools or set()

    def evaluate_tool_calls(
        self,
        tool_calls: List[ToolCall],
    ) -> List[ActionGuardViolation]:
        """Check a list of tool calls for authorization and human approval."""
        violations: List[ActionGuardViolation] = []

        for call in tool_calls:
            # 1. Allowlist verification
            if self.allowed_tools and call.name not in self.allowed_tools:
                violations.append(
                    ActionGuardViolation(
                        tool_name=call.name,
                        reason=f"Tool '{call.name}' is not in allowed tools list {list(self.allowed_tools)}",
                    )
                )

            # 2. Irreversible action verification
            is_irreversible = call.is_irreversible or (call.name in self.irreversible_tools)
            if is_irreversible and not call.human_approval_token:
                violations.append(
                    ActionGuardViolation(
                        tool_name=call.name,
                        reason=f"Irreversible tool '{call.name}' requires explicit human approval token",
                        is_irreversible=True,
                    )
                )

        return violations
