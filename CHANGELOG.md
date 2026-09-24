# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha] - 2026-09-24

### Added
- Foundational architectural and governance specifications:
  - `PRODUCT_VISION.md`
  - `ARCHITECTURE.md`
  - `THREAT_MODEL.md`
  - `EVALUATION_METHOD.md`
  - `IMPLEMENTATION_PLAN.md`
  - `DISCLAIMER.md`, `SECURITY.md`, `CONTRIBUTING.md`, `THIRD_PARTY_NOTICES.md`
- Initial project structure supporting `src/` layout and typed Python.
- MVP core modules: `gateway`, `evaluators`, `judges`, `guardrails`, `policies`, `monitoring`, `finops`, `evidence`, `integrations`.
- JSON Schemas:
  - `schemas/agent-spec.schema.json`
  - `schemas/policy.schema.json`
  - `schemas/evidence-receipt.schema.json`
- CLI command: `agentguard evaluate <path>` with exit code policy enforcement.
- Standalone HTML audit report generator and JSON cryptographic receipts.
- Synthetic customer-support evaluation benchmark suite.
