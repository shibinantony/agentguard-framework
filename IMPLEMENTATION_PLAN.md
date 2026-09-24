# AgentGuard Framework — MVP Implementation Plan & Acceptance Criteria

**Version:** 0.1.0-alpha  
**Status:** Approved for Implementation  
**Classification:** Independent Open-Source Project

---

## 1. Project Phasing

- **Phase 0: Architecture, Legal & Governance Baseline** *(Completed)*
  - Establish `PRODUCT_VISION.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`, `EVALUATION_METHOD.md`.
  - Establish `DISCLAIMER.md`, `SECURITY.md`, `CONTRIBUTING.md`, `THIRD_PARTY_NOTICES.md`, `LICENSE`.
- **Phase 1: Project Scaffolding & Core Schemas**
  - Setup `pyproject.toml` using `src/` layout with typed Python (3.10+).
  - Define JSON Schemas under `schemas/`:
    - `schemas/agent-spec.schema.json`
    - `schemas/policy.schema.json`
    - `schemas/evidence-receipt.schema.json`
- **Phase 2: Core Module Implementation**
  - `src/agentguard/integrations`: `ModelAdapter` abstract base class, `MockModelAdapter`.
  - `src/agentguard/guardrails`: `InjectionDetector`, `SensitiveDataDetector`, `ActionGuard`.
  - `src/agentguard/judges`: `Rubric`, `LLMJudge`, `MockJudge`.
  - `src/agentguard/finops`: Token tracking, cost model, retry waste, cost per successful task.
  - `src/agentguard/policies`: YAML policy parser and rule engine (PASS, REVIEW, BLOCK).
  - `src/agentguard/monitoring`: Redacting structured logger, latency timer, loop detector.
  - `src/agentguard/evidence`: JSON receipt generator (with SHA-256 integrity hash) and HTML report renderer.
  - `src/agentguard/evaluators`: Scenario loader and execution harness.
  - `src/agentguard/gateway`: Agent invocation wrapper and lifecycle coordinator.
- **Phase 3: CLI & Example Pack**
  - Implement CLI command: `agentguard evaluate <path>` using `argparse` or `click`.
  - Create `examples/customer-support-agent/` containing:
    - `agent.yaml`: Synthetic agent metadata and tool specs.
    - `scenarios.yaml`: Diverse synthetic test cases (positive resolution, prompt injection attempt, credential leak attempt, unauthorized tool attempt, borderline quality).
    - `policy.yaml`: Release gate rules (thresholds for PASS, REVIEW, BLOCK).
    - `rubrics/quality_rubric.yaml`: Versioned evaluation rubric.
- **Phase 4: CI/CD, Quality & Verification**
  - GitHub Actions workflow (`.github/workflows/ci.yml`).
  - Pre-commit configuration (`.pre-commit-config.yaml`).
  - Comprehensive pytest unit and integration test suite.
  - Verification:
    - Run all unit tests with 100% offline execution.
    - Run `agentguard evaluate examples/customer-support-agent`.
    - Validate output JSON receipt against `schemas/evidence-receipt.schema.json`.
    - Verify HTML report generation and structure.
    - Run automated secret scan.

---

## 2. Explicit MVP Acceptance Criteria

| ID | Category | Acceptance Criterion | Verification Method |
| :--- | :--- | :--- | :--- |
| **AC-01** | **CLI Command** | Running `agentguard evaluate examples/customer-support-agent` executes the evaluation suite from end to end. | Command execution in terminal. |
| **AC-02** | **Zero Network** | Default test execution and evaluation run 100% offline without network calls or API keys, using `MockModelAdapter` and `MockJudge`. | Socket disconnection / offline test verification. |
| **AC-03** | **Synthetic Scenarios** | Test dataset loads at least 5 synthetic scenarios covering: benign inquiry, prompt injection attack, secret leakage, unauthorized tool call, and poor response quality. | `scenarios.yaml` inspection and scenario runner log. |
| **AC-04** | **Deterministic Safety** | Detects prompt injection patterns and secret/PII patterns deterministically, immediately flagging violations. | Unit tests in `test_guardrails.py` and scenario results. |
| **AC-05** | **LLM Judge** | Executes evaluation against versioned rubric `customer-support-quality-v1.0.0` and produces structured score + rationale. | Unit tests in `test_judges.py`. |
| **AC-06** | **FinOps Metrics** | Accurately calculates prompt tokens, completion tokens, estimated cost (USD), latency (ms), retries, and **Cost per Successful Task**. | Unit tests in `test_finops.py` and evidence JSON output. |
| **AC-07** | **Policy Gating** | Emits `PASS`, `REVIEW`, or `BLOCK` according to `policy.yaml` thresholds. | Assertion in test cases for each scenario type. |
| **AC-08** | **Exit Code** | Returns exit code `0` on `PASS` / `REVIEW`, and non-zero exit code `1` when release-blocking policies fail. | Shell exit code check (`$LASTEXITCODE`). |
| **AC-09** | **JSON Evidence** | Produces a structured JSON receipt with SHA-256 fingerprint that strictly validates against `schemas/evidence-receipt.schema.json`. | Schema validation via `jsonschema`. |
| **AC-10** | **HTML Report** | Generates a styled, self-contained HTML audit report (`evidence.html`) displaying summary cards, scenario breakdown, FinOps charts/metrics, and cryptographic hashes. | File inspection and browser render test. |
| **AC-11** | **Structured Logging** | Logs are structured and all sensitive tokens or keys are redacted before writing. | Log stream inspection in tests. |
| **AC-12** | **Secret Hygiene** | Automated scan confirms no production keys, passwords, or confidential materials exist in repo. | Secret scanner execution. |

---

## 3. Directory Layout Specification

```
agentguard-framework/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── PRODUCT_VISION.md
│   ├── ARCHITECTURE.md
│   ├── THREAT_MODEL.md
│   ├── EVALUATION_METHOD.md
│   └── IMPLEMENTATION_PLAN.md
├── examples/
│   └── customer-support-agent/
│       ├── agent.yaml
│       ├── scenarios.yaml
│       ├── policy.yaml
│       └── rubrics/
│           └── quality_rubric.yaml
├── schemas/
│   ├── agent-spec.schema.json
│   ├── policy.schema.json
│   └── evidence-receipt.schema.json
├── src/
│   └── agentguard/
│       ├── __init__.py
│       ├── cli.py
│       ├── gateway/
│       │   ├── __init__.py
│       │   └── interceptor.py
│       ├── evaluators/
│       │   ├── __init__.py
│       │   └── runner.py
│       ├── judges/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── mock_judge.py
│       ├── guardrails/
│       │   ├── __init__.py
│       │   ├── injection.py
│       │   ├── sensitive_data.py
│       │   └── action_guard.py
│       ├── policies/
│       │   ├── __init__.py
│       │   └── engine.py
│       ├── monitoring/
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   └── telemetry.py
│       ├── finops/
│       │   ├── __init__.py
│       │   └── calculator.py
│       ├── evidence/
│       │   ├── __init__.py
│       │   ├── receipt.py
│       │   └── html_report.py
│       └── integrations/
│           ├── __init__.py
│           ├── base.py
│           └── mock_adapter.py
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_evaluators.py
│   ├── test_evidence.py
│   ├── test_finops.py
│   ├── test_guardrails.py
│   ├── test_judges.py
│   └── test_policies.py
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── DISCLAIMER.md
├── LICENSE
├── pyproject.toml
├── README.md
├── SECURITY.md
└── THIRD_PARTY_NOTICES.md
```
