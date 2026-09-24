"""Versioned rubrics and abstract judge interfaces."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Rubric(BaseModel):
    rubric_id: str
    version: str
    scale: List[int] = Field(default_factory=lambda: [1, 5])
    passing_score: float = 3.5
    criteria: Dict[Any, str] = Field(default_factory=dict)
    name: str = "Evaluation Rubric"
    description: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.criteria:
            self.criteria = {str(k): v for k, v in self.criteria.items()}



class JudgeResult(BaseModel):
    rubric_id: str
    rubric_version: str
    score: float = Field(ge=1.0, le=5.0)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    is_passing: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseJudge(ABC):
    """Abstract base class for all semantic LLM judges."""

    def __init__(self, rubric: Optional[Rubric] = None):
        self.rubric = rubric

    @abstractmethod
    def evaluate(
        self,
        prompt: str,
        response: str,
        ground_truth: str = "",
        rubric: Optional[Rubric] = None,
        **kwargs: Any,
    ) -> JudgeResult:
        """Evaluate agent response against the rubric."""
        pass
