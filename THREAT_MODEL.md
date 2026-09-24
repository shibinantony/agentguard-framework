# AgentGuard Framework — Threat Model

**Version:** 0.1.0-alpha  
**Status:** Approved Security Baseline  
**Frameworks Referenced:** STRIDE, OWASP Top 10 for LLM Applications (2025/2026), NIST AI 100-2e2025  
**Classification:** Independent Open-Source Project

---

## 1. Scope & System Boundaries

The scope of this threat model encompasses:
- The **AgentGuard CLI & SDK** runtime.
- **Evaluation Pipeline** (scenario ingestion, model execution, scoring).
- **Guardrails Engine** (deterministic pre- and post-execution filters).
- **Evidence Storage & Formatting** (JSON receipts, local HTML logs).

### Trust Boundaries
1. **User / Evaluator Input Boundary:** Untrusted synthetic or real inputs submitted to the agent.
2. **Model Provider Boundary:** External or mock model endpoints that may generate hallucinated, toxic, or adversarial outputs.
3. **Tool Execution Boundary:** Execution of external capabilities, APIs, or database queries initiated by the agent.
4. **Audit Evidence Boundary:** Storage of evaluation records that must be protected against tampering or covert modification.

---

## 2. Threat Analysis (OWASP LLM & STRIDE Mapping)

| Threat ID | Threat Name | STRIDE Category | OWASP LLM Ref | Description | Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TH-01** | Direct Prompt Injection | Tampering / Elevation of Privilege | LLM01: Prompt Injection | Adversarial payload in user prompt overrides system instructions or forces unauthorized actions. | **Critical** |
| **TH-02** | Credential & Secret Leakage | Information Disclosure | LLM06: Sensitive Info Disclosure | Agent outputs API keys, private keys, database credentials, or system tokens into responses or logs. | **Critical** |
| **TH-03** | PII Ingestion / Exposure | Information Disclosure | LLM06: Sensitive Info Disclosure | User prompt contains unmasked PII (SSN, credit card, phone) that is echoed back or written to unencrypted logs. | **High** |
| **TH-04** | Excessive Agency / Tool Hijack | Elevation of Privilege | LLM08: Excessive Agency | Agent invokes destructive or unauthorized tools without human approval (e.g. deletion, refunds > limit). | **High** |
| **TH-05** | Denial of Wallet (Runaway Loops)| Denial of Service | LLM04: Model DoS / Resource Exhaustion | Recursive agent tool loops generate excessive LLM calls, draining budgets or exhausting compute limits. | **High** |
| **TH-06** | Judge Evasion & Manipulation | Tampering | LLM01 / Evasion | Agent crafts responses specifically designed to exploit LLM-as-judge heuristics or trick prompt judges. | **Medium** |
| **TH-07** | Evidence Tampering | Tampering / Repudiation | Repudiation | Malicious or buggy actor alters generated evaluation records to falsely pass compliance gates. | **High** |
| **TH-08** | Insecure Log Exposure | Information Disclosure | Sensitive Logging | AgentGuard itself logs raw prompts or credentials in plaintext to terminal or file logs. | **High** |

---

## 3. Mitigation Strategies & Security Controls

```
+────────────────────────+─────────────────────────────────────────────────────────────+
| Threat                 | AgentGuard Control Implementation                           |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Direct Prompt Injection| `guardrails.InjectionDetector`:                             |
| (TH-01)                | - Compiled regex patterns for system prompt overrides       |
|                        | - Jailbreak signature detection ("ignore instructions")     |
|                        | - Immediate policy flag resulting in BLOCK verdict          |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Secret Leakage         | `guardrails.SensitiveDataDetector`:                         |
| (TH-02)                | - High-entropy string detection                             |
|                        | - Pattern matching for known keys (AWS, GitHub, Bearer)     |
|                        | - Immediate output redaction + BLOCK verdict                |
+────────────────────────+─────────────────────────────────────────────────────────────+
| PII Exposure           | `guardrails.SensitiveDataDetector`:                         |
| (TH-03)                | - Deterministic regex for email, credit cards, phones       |
|                        | - Configurable masking before logging or storage            |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Excessive Agency       | `guardrails.ActionGuard`:                                   |
| (TH-04)                | - Strict tool allowlist enforcement                         |
|                        | - Flagging and blocking irreversible operations             |
|                        | - Requiring explicit Human-In-The-Loop (HITL) approval flag |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Denial of Wallet       | `monitoring.LoopDetector` & `finops.FinOpsEngine`:          |
| (TH-05)                | - Hard limit on maximum tool recursion depth (e.g. max 5)   |
|                        | - Per-scenario token ceiling                                |
|                        | - Cost computation and retry waste attribution              |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Judge Evasion          | `judges.LLMJudge`:                                          |
| (TH-06)                | - Dual-tier evaluation: deterministic rules execute first   |
|                        | - Strict JSON structured outputs with confidence scoring    |
|                        | - Confidence threshold triggers human review                |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Evidence Tampering     | `evidence.EvidenceEngine`:                                  |
| (TH-07)                | - Canonical JSON serialization with SHA-256 integrity hash  |
|                        | - Verification routine checks hash match on reload          |
+────────────────────────+─────────────────────────────────────────────────────────────+
| Insecure Log Exposure  | `monitoring.RedactingLogger`:                               |
| (TH-08)                | - Formatter automatically masks API keys and tokens         |
|                        | - Output redaction applied to terminal and file streams     |
+────────────────────────+─────────────────────────────────────────────────────────────+
```

---

## 4. Human-in-the-Loop (HITL) & Irreversible Action Protocol

AgentGuard implements a strict boundary for irreversible or high-impact actions:

1. **Definition of High-Impact Actions:**
   - Financial disbursements, refunds, or order cancellations above a configurable threshold.
   - Deletion, modification of user permissions, or execution of arbitrary code/scripts.
   - Sending external unreviewed communications (e.g. mass emails).

2. **Protocol Rule:**
   - Any scenario where an agent invokes an irreversible tool without an explicit `human_approval_token` is categorized as a policy breach and assigned status `BLOCK` or `REVIEW`.

---

## 5. Security Scanning & Dependency Hygiene

- **Zero Untrusted Dependencies:** Only minimal, permissively licensed (MIT, Apache-2.0, BSD) dependencies are allowed.
- **Static Secret Scanning:** Automated scans across source files, examples, and test cases ensure no real credentials or keys are committed.
- **No Network in Default Tests:** Offline mock adapters prevent exfiltration vulnerabilities during CI/CD test runs.
