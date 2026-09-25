"""Production Live LLM-as-a-Judge for semantic, non-deterministic quality evaluation."""

from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Optional
from .base import BaseJudge, JudgeResult, Rubric
from ..integrations.base import ModelAdapter


JUDGE_SYSTEM_PROMPT = """You are an expert, impartial AI assurance judge.
Your task is to evaluate the quality, factual correctness, helpfulness, and policy adherence of an AI agent's response against an explicit scoring rubric.

CRITICAL INSTRUCTIONS:
1. Follow the rubric criteria strictly.
2. Provide step-by-step reasoning BEFORE assigning a score to prevent hallucination.
3. Be objective and do not reward unnecessary verbosity or superficial politeness.
4. Output your evaluation STRICTLY as a valid JSON object matching this schema:
{
  "reasoning": "string with thorough evaluation against rubric criteria",
  "score": float between 1.0 and 5.0,
  "confidence": float between 0.0 and 1.0
}
DO NOT output any markdown backticks, prose before or after, only the raw JSON.
"""


class APIJudge(BaseJudge):
    """Semantic LLM Judge executing live model prompts against versioned rubrics."""

    def __init__(
        self,
        model_adapter: ModelAdapter,
        rubric: Optional[Rubric] = None,
        samples: int = 1,
    ):
        super().__init__(rubric)
        self.adapter = model_adapter
        self.samples = max(1, samples)

    def _build_evaluation_prompt(
        self,
        prompt: str,
        response: str,
        ground_truth: str,
        rubric: Rubric,
    ) -> str:
        criteria_str = "\n".join(
            [f"  - Score {k}: {v}" for k, v in rubric.criteria.items()]
        )
        return f"""EVALUATION TASK:
Target Rubric: {rubric.name} (Version: {rubric.version})
Passing Threshold: {rubric.passing_score} / 5.0

Rubric Scoring Criteria:
{criteria_str}

User Prompt:
\"\"\"{prompt}\"\"\"

Agent Response to Evaluate:
\"\"\"{response}\"\"\"

Expected Ground Truth / Reference:
\"\"\"{ground_truth if ground_truth else 'N/A'}\"\"\"

Evaluate the Agent Response strictly according to the criteria above. Output your verdict in JSON."""

    def evaluate(
        self,
        prompt: str,
        response: str,
        ground_truth: str = "",
        rubric: Optional[Rubric] = None,
        **kwargs: Any,
    ) -> JudgeResult:
        active_rubric = rubric or self.rubric or Rubric(
            rubric_id="general-quality",
            version="1.0.0",
            passing_score=3.5,
        )

        eval_prompt = self._build_evaluation_prompt(
            prompt=prompt,
            response=response,
            ground_truth=ground_truth,
            rubric=active_rubric,
        )

        scores: List[float] = []
        confidences: List[float] = []
        rationales: List[str] = []

        for _ in range(self.samples):
            model_resp = self.adapter.generate(
                prompt=eval_prompt,
                system_prompt=JUDGE_SYSTEM_PROMPT,
                temperature=0.0,
            )
            raw_text = model_resp.content.strip()

            # Strip markdown fence if model returned ```json ... ```
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)
            raw_text = raw_text.strip()

            try:
                parsed = json.loads(raw_text)
                score = float(parsed.get("score", 3.0))
                confidence = float(parsed.get("confidence", 0.8))
                reasoning = parsed.get("reasoning", "Semantic judge evaluation completed.")
            except Exception:
                # Heuristic fallback if JSON parser encountered malformed string
                score = 3.0
                confidence = 0.5
                reasoning = f"Raw judge output: {raw_text[:200]}"

            scores.append(score)
            confidences.append(confidence)
            rationales.append(reasoning)

        # Aggregate across samples
        final_score = round(sum(scores) / len(scores), 2)
        final_confidence = round(sum(confidences) / len(confidences), 2)
        combined_rationale = rationales[0]
        if len(rationales) > 1:
            combined_rationale = f"Multi-Sample Consensus (avg score: {final_score}): {rationales[0]}"

        is_passing = final_score >= active_rubric.passing_score

        return JudgeResult(
            rubric_id=active_rubric.rubric_id,
            rubric_version=active_rubric.version,
            score=final_score,
            confidence=final_confidence,
            rationale=combined_rationale,
            is_passing=is_passing,
            metadata={
                "samples": self.samples,
                "score_variance": 0.0 if len(scores) == 1 else round(max(scores) - min(scores), 2),
            },
        )
