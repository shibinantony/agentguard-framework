"""Deterministic Mock Judge for offline testing and synthetic evaluation."""

from __future__ import annotations
from typing import Any, Dict, Optional
from .base import BaseJudge, JudgeResult, Rubric


class MockJudge(BaseJudge):
    """Deterministic offline judge evaluating quality and adherence to ground truth."""

    def __init__(
        self,
        rubric: Optional[Rubric] = None,
        default_score: float = 4.5,
        default_confidence: float = 0.95,
        default_rationale: str = "Response directly answers user prompt with high clarity and accuracy.",
    ):
        super().__init__(rubric)
        self.default_score = default_score
        self.default_confidence = default_confidence
        self.default_rationale = default_rationale
        self.custom_evaluations: Dict[str, JudgeResult] = {}

    def register_evaluation(self, key: str, result: JudgeResult) -> None:
        self.custom_evaluations[key] = result

    def evaluate(
        self,
        prompt: str,
        response: str,
        ground_truth: str = "",
        rubric: Optional[Rubric] = None,
        **kwargs: Any,
    ) -> JudgeResult:
        active_rubric = rubric or self.rubric or Rubric(
            rubric_id="default-rubric",
            version="1.0.0",
            passing_score=3.5,
        )

        # Check registered custom evaluations
        for key, res in self.custom_evaluations.items():
            if key.lower() in prompt.lower() or key.lower() in response.lower():
                return res

        # Deterministic heuristic scoring
        response_lower = response.lower()
        
        # Severe quality degradation signals
        if any(term in response_lower for term in ["i don't care", "shut up", "totally wrong", "nonsense response"]):
            score = 1.0
            confidence = 0.98
            rationale = "Response is unacceptable, hostile, or completely unhelpful."
        elif any(term in response_lower for term in ["maybe", "confused", "incomplete information", "sorry, i cannot"]):
            score = 2.5
            confidence = 0.85
            rationale = "Response lacks key customer requirements and provides incomplete information."
        elif ground_truth:
            # Check overlap with key words in ground truth
            gt_words = set(re_tokenize(ground_truth.lower()))
            resp_words = set(re_tokenize(response_lower))
            overlap = len(gt_words.intersection(resp_words)) / max(len(gt_words), 1)
            
            if overlap >= 0.5:
                score = 4.8
                confidence = 0.95
                rationale = f"Response matches ground truth expectations with high factual alignment (overlap ratio: {overlap:.2f})."
            else:
                score = 3.0
                confidence = 0.70
                rationale = f"Response partially aligns with ground truth expectations but misses specific keywords (overlap ratio: {overlap:.2f})."
        else:
            score = self.default_score
            confidence = self.default_confidence
            rationale = self.default_rationale

        is_passing = score >= active_rubric.passing_score
        return JudgeResult(
            rubric_id=active_rubric.rubric_id,
            rubric_version=active_rubric.version,
            score=score,
            confidence=confidence,
            rationale=rationale,
            is_passing=is_passing,
        )


def re_tokenize(text: str) -> list[str]:
    import re
    return re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text)
