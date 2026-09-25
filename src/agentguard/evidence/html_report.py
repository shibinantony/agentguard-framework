"""Local Standalone HTML Audit Report Generator."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
from jinja2 import Template


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentGuard Assurance Evidence Report - {{ receipt.receipt_id }}</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --pass: #10b981;
      --review: #f59e0b;
      --block: #ef4444;
      --primary: #3b82f6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 2rem;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }
    .badge {
      display: inline-block;
      padding: 0.4rem 1rem;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-PASS { background-color: rgba(16, 185, 129, 0.2); color: var(--pass); border: 1px solid var(--pass); }
    .badge-REVIEW { background-color: rgba(245, 158, 11, 0.2); color: var(--review); border: 1px solid var(--review); }
    .badge-BLOCK { background-color: rgba(239, 68, 68, 0.2); color: var(--block); border: 1px solid var(--block); }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
    }
    .card-title { font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .card-value { font-size: 1.75rem; font-weight: 700; margin-top: 0.5rem; }
    
    section { margin-bottom: 2.5rem; }
    h2 { font-size: 1.25rem; margin-bottom: 1rem; border-left: 4px solid var(--primary); padding-left: 0.75rem; }
    
    table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; }
    th, td { padding: 0.85rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { background: #162032; font-size: 0.85rem; color: var(--muted); text-transform: uppercase; }
    tr:last-child td { border-bottom: none; }
    
    .integrity-box {
      background: #020617;
      border: 1px dashed var(--border);
      border-radius: 6px;
      padding: 1rem;
      font-family: monospace;
      font-size: 0.85rem;
      color: #38bdf8;
      word-break: break-all;
    }
    .meta-row { display: flex; gap: 2rem; color: var(--muted); font-size: 0.9rem; margin-top: 0.5rem; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>AgentGuard Assurance Evidence Report</h1>
        <div class="meta-row">
          <span>Agent: <strong>{{ receipt.agent_id }}</strong></span>
          <span>Policy: <strong>{{ receipt.policy_id }}</strong></span>
          <span>Framework: <strong>{{ receipt.framework_version }}</strong></span>
          <span>Timestamp: <strong>{{ receipt.timestamp }}</strong></span>
        </div>
      </div>
      <div>
        <span class="badge badge-{{ receipt.verdict }}">{{ receipt.verdict }}</span>
      </div>
    </header>

    <section>
      <h2>Assurance & FinOps Summary</h2>
      <div class="grid">
        <div class="card">
          <div class="card-title">Scenarios Passed</div>
          <div class="card-value" style="color: var(--pass);">{{ receipt.summary.passed_scenarios }} / {{ receipt.summary.total_scenarios }}</div>
        </div>
        <div class="card">
          <div class="card-title">Mean Quality Score</div>
          <div class="card-value">{{ "%.2f"|format(receipt.summary.mean_quality_score) }} / 5.0</div>
        </div>
        <div class="card">
          <div class="card-title">Total Tokens</div>
          <div class="card-value">{{ receipt.summary.total_tokens }}</div>
        </div>
        <div class="card">
          <div class="card-title">Total Cost (USD)</div>
          <div class="card-value">${{ "%.5f"|format(receipt.summary.total_cost_usd) }}</div>
        </div>
        <div class="card">
          <div class="card-title">Cost / Successful Task</div>
          <div class="card-value" style="color: #38bdf8;">${{ "%.5f"|format(receipt.summary.cost_per_successful_task_usd) }}</div>
        </div>
        <div class="card">
          <div class="card-title">Mean Latency</div>
          <div class="card-value">{{ "%.1f"|format(receipt.summary.mean_latency_ms) }} ms</div>
        </div>
      </div>
    </section>

    <section>
      <h2>Scenario Evaluation Details</h2>
      <table>
        <thead>
          <tr>
            <th>Scenario ID</th>
            <th>Name</th>
            <th>Verdict</th>
            <th>Safety Checks</th>
            <th>Judge Score</th>
            <th>Cost (USD)</th>
            <th>Latency</th>
          </tr>
        </thead>
        <tbody>
          {% for s in receipt.scenarios %}
          <tr>
            <td><code>{{ s.scenario_id }}</code></td>
            <td><strong>{{ s.name }}</strong></td>
            <td><span class="badge badge-{{ s.verdict }}">{{ s.verdict }}</span></td>
            <td>
              {% if s.safety_checks.injection_detected %}
                <span style="color: var(--block);">Injection Triggered</span><br>
              {% endif %}
              {% if s.safety_checks.sensitive_data_detected %}
                <span style="color: var(--block);">Sensitive Data Found</span><br>
              {% endif %}
              {% if s.safety_checks.unauthorized_tools %}
                <span style="color: var(--block);">Unauthorized Tools</span><br>
              {% endif %}
              {% if s.safety_checks.unapproved_irreversible_actions %}
                <span style="color: var(--block);">Unapproved Action</span><br>
              {% endif %}
              {% if not s.safety_checks.injection_detected and not s.safety_checks.sensitive_data_detected and not s.safety_checks.unauthorized_tools and not s.safety_checks.unapproved_irreversible_actions %}
                <span style="color: var(--pass);">Clean</span>
              {% endif %}
            </td>
            <td>
              {% if s.judge_evaluation %}
                {{ "%.2f"|format(s.judge_evaluation.score) }} (conf: {{ "%.2f"|format(s.judge_evaluation.confidence) }})
              {% else %}
                <span style="color: var(--muted);">Skipped (Safety Gate)</span>
              {% endif %}
            </td>
            <td>${{ "%.5f"|format(s.finops.cost_usd) }}</td>
            <td>{{ s.finops.latency_ms }} ms</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Tamper-Evident Verification & Audit Provenance</h2>
      <div class="integrity-box">
        <div>Verification Standard: {{ receipt.integrity.algorithm }} Digest</div>
        <div>Audit Receipt Reference: {{ receipt.receipt_id }}</div>
        <div>Digital Verification Hash: {{ receipt.integrity.canonical_hash }}</div>
      </div>
    </section>
  </div>
</body>
</html>
"""


class HTMLReportRenderer:
    """Renders standalone HTML audit reports from evidence receipts."""

    def __init__(self) -> None:
        self.template = Template(HTML_TEMPLATE)

    def render(self, receipt: Dict[str, Any]) -> str:
        return self.template.render(receipt=receipt)

    def save_report(self, receipt: Dict[str, Any], output_path: Path) -> Path:
        html_content = self.render(receipt)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path
