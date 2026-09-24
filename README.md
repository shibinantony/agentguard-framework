# AgentGuard Framework

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](https://www.python.org/)

**AgentGuard Framework** is an independent, vendor-neutral assurance control plane for AI agents. It evaluates quality, enforces deterministic safety policies, tracks FinOps costs and token efficiency, monitors agent behaviour, and generates audit-ready cryptographic evidence receipts.

---

## Key Features

- **Vendor-Neutral Control Plane:** Model-agnostic architecture with pluggable adapters and an offline mock runner.
- **Dual-Tier Assurance:** Microsecond deterministic guardrails (prompt injection, PII, secret leakage, unauthorized tool calls) paired with calibrated semantic LLM-as-a-judge rubrics.
- **Policy-as-Code Gating:** Declarative release policies yielding `PASS`, `REVIEW`, or `BLOCK` with CI/CD exit codes.
- **Agentic FinOps:** Measures token consumption, pricing, loop/retry waste, and **Cost per Successful Task**.
- **Audit-Ready Evidence:** Emits SHA-256 fingerprint-verified JSON receipts and self-contained HTML audit reports.
- **Clean-Room & Privacy First:** Built with 100% original code, permissive dependencies, and synthetic test datasets.

---

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/shibinantony/agentguard-framework.git
cd agentguard-framework

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Run Evaluation

Evaluate the synthetic customer-support agent benchmark:

```bash
agentguard evaluate examples/customer-support-agent
```

---

## Documentation

- [Product Vision](docs/PRODUCT_VISION.md)
- [Architecture & Data Flows](docs/ARCHITECTURE.md)
- [Threat Model](docs/THREAT_MODEL.md)
- [Evaluation Methodology](docs/EVALUATION_METHOD.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Disclaimer](DISCLAIMER.md)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Third-Party Notices](THIRD_PARTY_NOTICES.md)

---

## License

AgentGuard Framework is licensed under the [Apache License 2.0](LICENSE).
