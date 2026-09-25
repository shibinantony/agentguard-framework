# AgentGuard Framework

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![CI](https://github.com/shibinantony/agentguard-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/shibinantony/agentguard-framework/actions/workflows/ci.yml)

> **"From Reactive Governance to Engineered Trust."**  
> *Transforming AI compliance and safety from manual, episodic audit gates into autonomous, continuous, in-pipeline assurance.*

---

## 1. Executive Summary: Why AgentGuard Exists

Enterprise AI adoption stalls when conversations open with *"how do we stop hallucinations?"*

The real obstacle is **ungoverned non-determinism reaching production decisions**. When an autonomous agent plans multi-step tool calls, accesses enterprise databases, and generates customer-facing actions, traditional static prompt evaluations fall short. The true operational risk is not simply a faulty response—it is the **inability to prove why an agentic action was permitted, what guardrails were evaluated, and how much it cost**.

**AgentGuard Framework** is an independent, vendor-neutral assurance control plane that:
1. **Enforces Policy-as-Code**: Declarative release gates yielding unambiguous operational verdicts: `PASS`, `REVIEW`, or `BLOCK`.
2. **Pairs Deterministic Speed with Calibrated Semantic Evals**: Combines microsecond deterministic safety filters with multi-sample LLM-as-a-judge rubrics.
3. **Decouples Governance from Headcount**: Breaks the linear FTE model by running automated adversarial testing, red-teaming checks, and regression gates directly inside CI/CD pipelines.
4. **Calculates Agentic FinOps**: Provides actionable unit economics across major hyperscalers, quantifying retry waste, token burn, and **Cost per Successful Task**.
5. **Generates Tamper-Evident Evidence**: Emits digital verification receipts (SHA-256) and interactive HTML dashboards for auditors, risk officers, and engineering directors.

---

## 2. Core Architecture: Dual-Tier Assurance

```
                               Target AI Agent Workflow
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           AgentGuard Gateway & Runtime                            │
│  - Ingress / Egress Interception                                                  │
│  - Loop Detection & Runaway Recursion Circuit Breakers                           │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│    Tier 1: Deterministic Gates      │       │     Tier 2: Semantic LLM Judge      │
│  - Heuristic Injection Detector     │       │  - Versioned 1–5 Scoring Rubrics    │
│  - Secret & Credential Scanner      │       │  - Step-by-Step Chain-of-Thought    │
│  - PII Masking & Data Sanitizer     │       │  - Multi-Sample Consensus & Variance│
│  - Tool Whitelist & Action Guard    │       │  - Grey-Zone Human Review Routing   │
└──────────────────┬──────────────────┘       └──────────────────┬──────────────────┘
                   │                                             │
                   └──────────────────────┬──────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                               Policy-as-Code Engine                               │
│              Verdicts: PASS (0)  |  REVIEW (0 or 2)  |  BLOCK (1)                 │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│          FinOps Calculator          │       │    Tamper-Evident Evidence Chain    │
│  - Multi-Hyperscaler Rate Cards     │       │  - Canonical SHA-256 Audit Receipt  │
│  - Retry Waste Quantification       │       │  - Structured JSON Evidence Store   │
│  - Cost per Successful Task Metric  │       │  - Interactive HTML Audit Dashboard │
└─────────────────────────────────────┘       └─────────────────────────────────────┘
```

---

## 3. Resolving Non-Determinism in LLM-as-a-Judge

Semantic detection in natural language is inherently probabilistic. AgentGuard addresses the limitations of LLM judges through a disciplined calibration methodology:

1. **Step-by-Step Reasoning Prior to Scoring**: The judge model must generate rationale mapped against explicit rubric criteria before emitting numerical scores, mitigating verbosity and confirmation bias.
2. **Multi-Sample Variance Tracking (`--judge-samples N`)**: Run evaluations across multiple sampling passes to calculate score variance ($\sigma^2$) and detect borderline stability.
3. **Automated Grey-Zone Routing**: When a judge score falls within boundary zones (e.g. $\pm 0.5$ from threshold) or confidence drops below $80\%$, AgentGuard flags the scenario as `REVIEW`, inviting human sign-off rather than guessing.
4. **Deterministic Pre-Filtering**: Expensive, non-deterministic judge models are never invoked if microsecond deterministic checks (injection signatures, credential leaks, unapproved tools) are breached.

---

## 4. Multi-Hyperscaler FinOps Engine

AgentGuard provides ready-to-use, versioned pricing rate cards for major cloud hyperscalers in the [`finops-packs/`](finops-packs/) directory:

| Hyperscaler Pack | Target Models & Services | Rate Card File |
| :--- | :--- | :--- |
| **Microsoft Azure** | Azure OpenAI Service (GPT-4o, GPT-4o-mini, o1) | [`finops-packs/azure-openai-pricing.yaml`](finops-packs/azure-openai-pricing.yaml) |
| **Amazon Web Services (AWS)** | Amazon Bedrock (Claude 3.5 Sonnet, Claude 3 Haiku, Llama 3.1 70B, Titan) | [`finops-packs/aws-bedrock-pricing.yaml`](finops-packs/aws-bedrock-pricing.yaml) |
| **Google Cloud (GCP)** | Vertex AI (Gemini 1.5 Pro, Gemini 1.5 Flash, Claude on Vertex) | [`finops-packs/gcp-vertex-pricing.yaml`](finops-packs/gcp-vertex-pricing.yaml) |
| **OpenAI Direct** | OpenAI Platform API (GPT-4o, GPT-4o-mini, o1) | [`finops-packs/openai-pricing.yaml`](finops-packs/openai-pricing.yaml) |
| **Self-Hosted / Private Cloud** | vLLM / Triton on GPU clusters (Llama 3.1, Mistral amortized cost) | [`finops-packs/self-hosted-vllm-pricing.yaml`](finops-packs/self-hosted-vllm-pricing.yaml) |

### Key Metric: Cost per Successful Task
Traditional dashboards report total token expenditure. AgentGuard connects tokens to business outcomes:
$$\text{Cost per Successful Task} = \frac{\text{Total Pipeline Expenditure (USD)}}{\text{Number of Tasks Passing Both Quality and Safety Gates}}$$

This surfaces the true operational waste caused by recursive loops, unhandled retries, and failed agent runs.

---

## 5. Live Model API & Offline Testing Modes

AgentGuard operates flexibly in two modes:

### Mode A: 100% Offline & Deterministic (Default)
Ideal for CI/CD gates, local pull requests, and hermetic build systems.
- Zero network calls, zero API tokens required.
- Uses `MockModelAdapter` and `MockJudge` with synthetic fixtures.
- Guarantees $0.00$ external spend and instantaneous test execution.

### Mode B: Live Model API Testing (`--live`)
Connects directly to frontier commercial models or local self-hosted endpoints:
- **OpenAI / Azure OpenAI**: Set `OPENAI_API_KEY` (or `AZURE_OPENAI_API_KEY`).
- **Anthropic Claude**: Set `ANTHROPIC_API_KEY`.
- **Google Gemini / Vertex AI**: Set `GEMINI_API_KEY`.
- **Local vLLM / Ollama**: Set `LOCAL_API_KEY` and host endpoint.

---

## 6. Quickstart & Command-Line Usage

### Installation

```bash
# Clone the repository
git clone https://github.com/shibinantony/agentguard-framework.git
cd agentguard-framework

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Running Evaluations

#### 1. Baseline Offline Evaluation
```bash
agentguard evaluate examples/customer-support-agent
```

#### 2. Apply Hyperscaler FinOps Pricing (e.g. Azure OpenAI or AWS Bedrock)
```bash
agentguard evaluate examples/customer-support-agent --hyperscaler azure
agentguard evaluate examples/customer-support-agent --hyperscaler aws
```

#### 3. Live Model API Evaluation with Multi-Sample LLM Judging
```bash
export OPENAI_API_KEY="your-api-key"
agentguard evaluate examples/customer-support-agent --live --judge-samples 3
```

#### 4. Auto-Open Generated Interactive HTML Audit Report
```bash
agentguard evaluate examples/customer-support-agent --open
```

---

## 7. Audit Artifacts & Output Locations

All evaluation outputs are saved to the configured output directory (default: `./reports/`):

1. **Structured Tamper-Evident JSON Receipt**:  
   `./reports/evidence.json`  
   Contains complete scenario records, token breakdowns, timestamps, policy violations, and a canonical SHA-256 digital verification hash validated against [`schemas/evidence-receipt.schema.json`](schemas/evidence-receipt.schema.json).
2. **Interactive HTML Audit Report**:  
   `./reports/evidence.html`  
   A standalone, CSS-styled audit report ready for review by compliance committees, lead architects, and engineering managers without requiring any backend web server.

---

## 8. Strategic Alignment with Governance Frameworks

AgentGuard Framework aligns with the policy-as-code principles established in companion libraries:
- [shibinantony/ai-governance-as-code](https://github.com/shibinantony/ai-governance-as-code): Regulated-industry policy packs for BFSI and Pharma.
- [shibinantony/Trust_based_Responsible_AI](https://github.com/shibinantony/Trust_based_Responsible_AI): Transitioning AI governance from subjective risk avoidance to engineered trust.
- **Standards Addressed**: NIST AI RMF 1.0, ISO/IEC 42001, EU AI Act (High-Risk Agent Requirements), and OWASP Top 10 for LLM Applications (2025/2026).

---

## 9. Repository Structure

```
agentguard-framework/
├── docs/                                  # Executive Strategy & Architecture
│   ├── PRODUCT_VISION.md                  # Engineered trust & market positioning
│   ├── ARCHITECTURE.md                    # Control plane components & data flows
│   ├── THREAT_MODEL.md                    # STRIDE & OWASP LLM threat matrix
│   ├── EVALUATION_METHOD.md               # Deterministic + calibrated judge methodology
│   └── IMPLEMENTATION_PLAN.md             # Phasing & acceptance criteria
├── finops-packs/                          # Hyperscaler Pricing & Rate Cards
│   ├── azure-openai-pricing.yaml          # Microsoft Azure OpenAI
│   ├── aws-bedrock-pricing.yaml           # AWS Bedrock
│   ├── gcp-vertex-pricing.yaml            # Google Cloud Vertex AI
│   ├── openai-pricing.yaml                # OpenAI Direct
│   └── self-hosted-vllm-pricing.yaml      # Private GPU / vLLM
├── examples/customer-support-agent/       # Synthetic Reference Benchmark
│   ├── agent.yaml                         # Agent definition & tool specifications
│   ├── policy.yaml                        # Release gate thresholds (PASS/REVIEW/BLOCK)
│   ├── rubrics/quality_rubric.yaml        # Versioned 1–5 scoring rubric
│   └── scenarios.yaml                     # 7 adversarial & benign synthetic test cases
├── schemas/                               # JSON Schemas
│   ├── agent-spec.schema.json             # Agent card schema
│   ├── policy.schema.json                 # Policy definition schema
│   └── evidence-receipt.schema.json       # Audit evidence receipt schema
├── src/agentguard/                        # Core Python Engine
│   ├── cli.py                             # CLI entrypoint (agentguard evaluate)
│   ├── evaluators/                        # Test scenario runner
│   ├── evidence/                          # SHA-256 receipts & HTML report generator
│   ├── finops/                            # Token metering & hyperscaler calculator
│   ├── gateway/                           # Ingress/egress runtime proxy & loop detector
│   ├── guardrails/                        # Injection, secret/PII, and tool guards
│   ├── integrations/                      # Mock & Live API Model Adapters
│   ├── judges/                            # Base, Mock, and Live LLM Judge
│   ├── monitoring/                        # Redacting logger & runtime telemetry
│   └── policies/                          # Policy-as-Code evaluation engine
├── tests/                                 # Pytest Verification Suite (30 tests, 92%+ coverage)
├── .github/workflows/ci.yml               # Multi-Python GitHub Actions workflow
├── .pre-commit-config.yaml                # Pre-commit code hygiene
├── DISCLAIMER.md                          # Independent project & synthetic data notice
├── SECURITY.md                            # Responsible disclosure policy
├── CONTRIBUTING.md                        # Clean-room contribution guidelines
├── THIRD_PARTY_NOTICES.md                 # Dependency provenance & licenses
├── LICENSE                                # Apache License 2.0
└── pyproject.toml                         # Packaging specification
```

---

## 10. License

AgentGuard Framework is distributed under the [Apache License 2.0](LICENSE).
Documentation and reference specifications are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
