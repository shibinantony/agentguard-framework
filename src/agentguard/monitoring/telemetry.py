"""Telemetry tracking and runaway agent loop detection."""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    data: Dict[str, Any] = Field(default_factory=dict)


class LoopDetector:
    """Detects runaway tool invocation cycles and infinite recursion in agent sessions."""

    def __init__(self, max_consecutive_identical_calls: int = 3, max_total_calls: int = 15):
        self.max_consecutive_identical_calls = max_consecutive_identical_calls
        self.max_total_calls = max_total_calls
        self.call_history: List[str] = []

    def record_call(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a tool call. Returns True if a loop or recursion limit is breached.
        """
        call_signature = f"{tool_name}:{sorted((arguments or {}).items())}"
        self.call_history.append(call_signature)

        if len(self.call_history) > self.max_total_calls:
            return True

        if len(self.call_history) >= self.max_consecutive_identical_calls:
            recent = self.call_history[-self.max_consecutive_identical_calls:]
            if len(set(recent)) == 1:
                return True

        return False

    def reset(self) -> None:
        self.call_history.clear()


class TelemetryTracker:
    """Collects runtime operational telemetry across agent evaluation runs."""

    def __init__(self) -> None:
        self.events: List[TelemetryEvent] = []
        self._start_time: Optional[float] = None

    def start_timer(self) -> None:
        self._start_time = time.perf_counter()

    def stop_timer(self) -> float:
        if self._start_time is None:
            return 0.0
        elapsed_ms = (time.perf_counter() - self._start_time) * 1000.0
        self._start_time = None
        return round(elapsed_ms, 2)

    def record_event(self, event_type: str, **kwargs: Any) -> None:
        self.events.append(TelemetryEvent(event_type=event_type, data=kwargs))
