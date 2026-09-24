# Security Policy

## 1. Reporting a Vulnerability

The AgentGuard project team takes security vulnerabilities seriously. If you discover a security vulnerability in the AgentGuard Framework codebase, CLI, or default guardrail rules, please do **NOT** open a public issue on GitHub.

Instead, please send a responsible disclosure report to the maintainers at:
`security-advisory@agentguard.dev` (or open a confidential GitHub Security Advisory).

Please include:
- A description of the vulnerability.
- Steps to reproduce or a minimal proof-of-concept (using synthetic inputs only).
- Potential impact and affected versions.

We will acknowledge receipt within 48 hours and provide updates as the fix progresses.

---

## 2. Secrets & Credentials Policy

- **No Secrets in Code or Logs:** AgentGuard is designed to inspect, detect, and redact secrets, not store them. Never commit API keys, cloud credentials, tokens, or private certificates to this repository.
- **Redaction Default:** The built-in logging and evidence formatting modules are configured to redact known secret patterns automatically.
- **Automated Scanning:** Every commit is scanned with static secret detection routines in CI.

---

## 3. Supported Versions

| Version | Supported |
| :--- | :--- |
| `0.1.x` (MVP) | Yes (Current development branch) |
| `< 0.1.0` | No |
