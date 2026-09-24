# Contributing to AgentGuard Framework

Thank you for your interest in contributing to the AgentGuard Framework! We welcome community contributions to build open, vendor-neutral assurance infrastructure for AI agents.

---

## 1. Clean-Room & Ethical Contribution Requirements

To protect the independent integrity of this project, all contributors must strictly adhere to the following clean-room boundaries:

1. **Original Work Only:** Submit only your own original work or permissively licensed open-source contributions.
2. **No Employer or Client Material:** Do **NOT** contribute code, documentation, prompts, policies, or datasets derived from your employer, clients, proprietary systems, or confidential projects.
3. **Synthetic Data Only:** All test scenarios, sample inputs, and evaluation datasets must use 100% synthetic data.
4. **Permissive Licensing:** Any third-party library or dependency introduced must use a permissive open-source license (MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC).
5. **No Network Access in Core Tests:** Unit and evaluation tests must run offline using mock adapters.

---

## 2. Development Setup

Requirements:
- Python 3.10+
- Git

```bash
# Clone the repository
git clone https://github.com/shibinantony/agentguard-framework.git
cd agentguard-framework

# Create a virtual environment
py -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

---

## 3. Pull Request Guidelines

1. Ensure all existing tests pass (`pytest`).
2. Add new unit tests for any new modules, guardrail detectors, or policy rules.
3. Verify that running `agentguard evaluate examples/customer-support-agent` passes.
4. Run pre-commit checks and formatting (`black`, `flake8`, `mypy`).
5. Update `CHANGELOG.md` with your changes.
