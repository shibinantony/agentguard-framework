"""Evaluation harness and synthetic scenario runner."""

from __future__ import annotations
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

from ..evidence.receipt import EvidenceGenerator
from ..evidence.html_report import HTMLReportRenderer
from ..finops.calculator import FinOpsCalculator, TaskFinOps
from ..guardrails.action_guard import ActionGuard
from ..guardrails.injection import InjectionDetector
from ..guardrails.sensitive_data import SensitiveDataDetector
from ..integrations.base import ModelAdapter, ModelResponse, ToolCall
from ..integrations.mock_adapter import MockModelAdapter
from ..judges.base import BaseJudge, Rubric
from ..judges.mock_judge import MockJudge
from ..monitoring.telemetry import TelemetryTracker
from ..policies.engine import EvaluationVerdict, PolicyDefinition, PolicyEngine


class ScenarioItem(BaseModel):
    scenario_id: str
    name: str
    input_prompt: str
    expected_output: str = ""
    expected_tool_calls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    simulated_model_response: Optional[Dict[str, Any]] = None


class ScenarioRunner:
    """Executes synthetic scenario test suites against the assurance control plane."""

    def __init__(
        self,
        agent_config: Dict[str, Any],
        scenarios: List[ScenarioItem],
        policy: PolicyDefinition,
        rubric: Optional[Rubric] = None,
        model_adapter: Optional[ModelAdapter] = None,
        judge: Optional[BaseJudge] = None,
    ):
        self.agent_config = agent_config
        self.scenarios = scenarios
        self.policy = policy
        self.rubric = rubric or Rubric(
            rubric_id="customer-support-quality",
            version="1.0.0",
            passing_score=3.5,
        )

        # Setup adapters and evaluators
        self.model_adapter = model_adapter or MockModelAdapter()
        self.judge = judge or MockJudge(rubric=self.rubric)
        self.finops = FinOpsCalculator()
        self.policy_engine = PolicyEngine(self.policy)
        self.evidence_gen = EvidenceGenerator()
        self.html_renderer = HTMLReportRenderer()

        # Setup deterministic guardrails
        self.injection_detector = InjectionDetector()
        self.sensitive_detector = SensitiveDataDetector()

        allowed_tools = {t["name"] for t in self.agent_config.get("tools", [])}
        irreversible_tools = {
            t["name"] for t in self.agent_config.get("tools", []) if t.get("is_irreversible", False)
        }
        self.action_guard = ActionGuard(
            allowed_tools=allowed_tools,
            irreversible_tools=irreversible_tools,
        )

    @classmethod
    def from_directory(
        cls,
        dir_path: Path | str,
        live: bool = False,
        hyperscaler: Optional[str] = None,
        judge_samples: int = 1,
    ) -> ScenarioRunner:
        """Instantiate runner from an agent scenario directory."""
        dir_path = Path(dir_path)
        
        agent_path = dir_path / "agent.yaml"
        scenarios_path = dir_path / "scenarios.yaml"
        policy_path = dir_path / "policy.yaml"
        rubric_path = dir_path / "rubrics" / "quality_rubric.yaml"

        with open(agent_path, "r", encoding="utf-8") as f:
            agent_config = yaml.safe_load(f)

        with open(scenarios_path, "r", encoding="utf-8") as f:
            scenarios_raw = yaml.safe_load(f)
            scenarios = [ScenarioItem(**s) for s in scenarios_raw.get("scenarios", [])]

        policy = PolicyDefinition()
        if policy_path.exists():
            with open(policy_path, "r", encoding="utf-8") as f:
                policy_raw = yaml.safe_load(f)
                policy = PolicyDefinition(**policy_raw)

        rubric = None
        if rubric_path.exists():
            with open(rubric_path, "r", encoding="utf-8") as f:
                rubric_raw = yaml.safe_load(f)
                rubric = Rubric(**rubric_raw)

        canned_responses = {}
        for s in scenarios:
            if s.simulated_model_response:
                sim = s.simulated_model_response
                tools = [
                    ToolCall(
                        name=tc.get("name", ""),
                        arguments=tc.get("arguments", {}),
                        is_irreversible=tc.get("is_irreversible", False),
                        human_approval_token=tc.get("human_approval_token"),
                    )
                    for tc in sim.get("tool_calls", [])
                ]
                resp = ModelResponse(
                    content=sim.get("content", ""),
                    tool_calls=tools,
                    prompt_tokens=sim.get("prompt_tokens", 50),
                    completion_tokens=sim.get("completion_tokens", 30),
                    latency_ms=sim.get("latency_ms", 150.0),
                    retries=sim.get("retries", 0),
                    model_id=sim.get("model_id", "mock-agent-v1"),
                )
                canned_responses[s.input_prompt] = resp

        adapter = None
        judge = None

        model_spec = agent_config.get("model", {})
        provider = model_spec.get("provider", "mock").lower()

        if live or (provider != "mock" and provider != ""):
            from ..integrations.api_adapter import APIModelAdapter
            from ..judges.api_judge import APIJudge

            adapter = APIModelAdapter(
                provider=provider if provider != "mock" else "openai",
                model_id=model_spec.get("model_id", "gpt-4o-mini"),
            )
            judge = APIJudge(model_adapter=adapter, rubric=rubric, samples=judge_samples)
        else:
            adapter = MockModelAdapter(canned_responses=canned_responses)
            judge = MockJudge(rubric=rubric)

        finops_calc = FinOpsCalculator.from_hyperscaler(hyperscaler) if hyperscaler else FinOpsCalculator()

        runner = cls(
            agent_config=agent_config,
            scenarios=scenarios,
            policy=policy,
            rubric=rubric,
            model_adapter=adapter,
            judge=judge,
        )
        runner.finops = finops_calc
        return runner

    def run_all(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Execute all scenarios, generate evidence receipt, and render HTML report."""
        tracker = TelemetryTracker()
        scenario_results: List[Dict[str, Any]] = []
        task_finops_list: List[TaskFinOps] = []
        scenario_verdicts: List[EvaluationVerdict] = []
        quality_scores: List[float] = []

        system_prompt = self.agent_config.get("system_prompt", "")
        tools = self.agent_config.get("tools", [])

        for scenario in self.scenarios:
            tracker.start_timer()

            # 1. Pre-execution guardrails
            injection_matches = self.injection_detector.detect(scenario.input_prompt)
            in_pii = self.sensitive_detector.detect_all(scenario.input_prompt)

            injection_detected = len(injection_matches) > 0
            sensitive_in_detected = len(in_pii) > 0

            # 2. Invoke Model Adapter
            response = self.model_adapter.generate(
                prompt=scenario.input_prompt,
                system_prompt=system_prompt,
                tools=tools,
            )

            # 3. Post-execution guardrails
            out_sensitive = self.sensitive_detector.detect_all(response.content)
            sensitive_out_detected = len(out_sensitive) > 0
            sensitive_detected = sensitive_in_detected or sensitive_out_detected

            action_violations = self.action_guard.evaluate_tool_calls(response.tool_calls)
            unauthorized_tools = [
                v.tool_name for v in action_violations if not v.is_irreversible
            ]
            unapproved_actions = [
                v.tool_name for v in action_violations if v.is_irreversible
            ]

            # 4. Semantic Judge (Run if no critical injection)
            judge_res = None
            if not injection_detected and not sensitive_out_detected:
                judge_res = self.judge.evaluate(
                    prompt=scenario.input_prompt,
                    response=response.content,
                    ground_truth=scenario.expected_output,
                    rubric=self.rubric,
                )
                quality_scores.append(judge_res.score)

            judge_score = judge_res.score if judge_res else 1.0
            judge_confidence = judge_res.confidence if judge_res else 1.0

            # 5. Policy evaluation for scenario
            is_task_safe = not injection_detected and not sensitive_out_detected and not unauthorized_tools and not unapproved_actions
            is_task_successful = is_task_safe and (judge_res.is_passing if judge_res else False)

            scenario_verdict, violations = self.policy_engine.evaluate_scenario(
                injection_detected=injection_detected,
                sensitive_data_detected=sensitive_out_detected,
                unauthorized_tools_count=len(unauthorized_tools),
                unapproved_irreversible_count=len(unapproved_actions),
                judge_score=judge_score if judge_res else None,
                judge_confidence=judge_confidence if judge_res else None,
                latency_ms=response.latency_ms,
                cost_usd=self.finops.calculate_cost(response.prompt_tokens, response.completion_tokens, response.model_id),
            )
            scenario_verdicts.append(scenario_verdict)

            # 6. FinOps computation
            task_finops = self.finops.calculate_task_finops(
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=response.latency_ms,
                retries=response.retries,
                is_task_successful=is_task_successful,
                model_id=response.model_id,
            )
            task_finops_list.append(task_finops)

            # Assemble scenario record
            scenario_results.append({
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "verdict": scenario_verdict.value,
                "safety_checks": {
                    "injection_detected": injection_detected,
                    "injection_patterns": [m.pattern_name for m in injection_matches],
                    "sensitive_data_detected": sensitive_detected,
                    "sensitive_data_types": list({m.type_name for m in (in_pii + out_sensitive)}),
                    "unauthorized_tools": unauthorized_tools,
                    "unapproved_irreversible_actions": unapproved_actions,
                },
                "judge_evaluation": {
                    "rubric_id": self.rubric.rubric_id,
                    "rubric_version": self.rubric.version,
                    "score": round(judge_score, 2),
                    "confidence": round(judge_confidence, 2),
                    "rationale": judge_res.rationale if judge_res else "Skipped due to deterministic security violation.",
                } if judge_res else None,
                "finops": task_finops.model_dump(),
                "policy_violations": violations,
            })

        # Aggregate suite
        finops_agg = self.finops.aggregate(task_finops_list)
        mean_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        suite_verdict, suite_violations = self.policy_engine.evaluate_suite(
            scenario_verdicts=scenario_verdicts,
            mean_quality_score=mean_quality,
            cost_per_successful_task=finops_agg["cost_per_successful_task_usd"],
        )

        passed_scenarios_count = sum(1 for v in scenario_verdicts if v == EvaluationVerdict.PASS)
        failed_scenarios_count = len(scenario_verdicts) - passed_scenarios_count

        summary = {
            "total_scenarios": len(self.scenarios),
            "passed_scenarios": passed_scenarios_count,
            "failed_scenarios": failed_scenarios_count,
            "mean_quality_score": round(mean_quality, 2),
            "total_tokens": finops_agg["total_tokens"],
            "prompt_tokens": finops_agg["prompt_tokens"],
            "completion_tokens": finops_agg["completion_tokens"],
            "total_cost_usd": finops_agg["total_cost_usd"],
            "cost_per_successful_task_usd": finops_agg["cost_per_successful_task_usd"],
            "total_retries": finops_agg["total_retries"],
            "mean_latency_ms": finops_agg["mean_latency_ms"],
        }

        # Build cryptographic receipt
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt = self.evidence_gen.create_receipt(
            receipt_id=f"rcpt-{int(datetime.datetime.now().timestamp())}",
            timestamp=now_iso,
            framework_version="0.1.0",
            agent_id=self.agent_config.get("agent_id", "unknown-agent"),
            policy_id=self.policy.policy_id,
            verdict=suite_verdict.value,
            summary=summary,
            scenarios=scenario_results,
        )

        # Output persistence if requested
        if output_dir:
            output_dir = Path(output_dir)
            json_path = output_dir / "evidence.json"
            html_path = output_dir / "evidence.html"
            self.evidence_gen.save_receipt(receipt, json_path)
            self.html_renderer.save_report(receipt, html_path)
            receipt["artifacts"] = {
                "json_path": str(json_path.resolve()),
                "html_path": str(html_path.resolve()),
            }

        receipt["suite_violations"] = suite_violations
        return receipt
