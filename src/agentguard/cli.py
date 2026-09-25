"""AgentGuard CLI interface: Executive Assurance Control Plane for AI Agents."""

from __future__ import annotations
import sys
import webbrowser
from pathlib import Path
from typing import Optional
import click
from .evaluators.runner import ScenarioRunner
from .monitoring.logger import get_redacting_logger
from .policies.engine import EvaluationVerdict, PolicyEngine


@click.group()
@click.version_option(version="0.1.0", prog_name="agentguard")
def main() -> None:
    """AgentGuard: Vendor-neutral assurance control plane for AI agents."""
    pass


@main.command(name="evaluate")
@click.argument("target_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--output-dir", "-o", default="reports", help="Directory where audit receipts and HTML reports are saved (default: ./reports).")
@click.option("--strict", is_flag=True, default=False, help="Fail with non-zero exit code on REVIEW status (for zero-tolerance release gates).")
@click.option("--live", is_flag=True, default=False, help="Execute live LLM API calls instead of deterministic mock adapter.")
@click.option("--hyperscaler", "-h", type=click.Choice(["azure", "aws", "gcp", "openai", "vllm"], case_sensitive=False), default=None, help="Apply hyperscaler-specific FinOps pricing rate card.")
@click.option("--judge-samples", type=int, default=1, help="Number of LLM judge evaluation samples to calculate variance.")
@click.option("--open", "open_report", is_flag=True, default=False, help="Automatically open generated HTML audit report in default web browser.")
def evaluate(
    target_path: str,
    output_dir: str,
    strict: bool,
    live: bool,
    hyperscaler: Optional[str],
    judge_samples: int,
    open_report: bool,
) -> None:
    """Evaluate an AI agent scenario directory against assurance policies."""
    logger = get_redacting_logger("agentguard.cli")
    target = Path(target_path)
    output = Path(output_dir)

    click.echo(click.style(f"\n=======================================================", fg="cyan"))
    click.echo(click.style(f" AgentGuard Assurance Control Plane ", fg="cyan", bold=True))
    click.echo(click.style(f" Mode: {'LIVE MODEL API' if live else 'DETERMINISTIC MOCK'}", fg="yellow" if live else "green"))
    if hyperscaler:
        click.echo(click.style(f" FinOps Rate Card: {hyperscaler.upper()}", fg="cyan"))
    click.echo(click.style(f" Target: {target.resolve()}", fg="cyan"))
    click.echo(click.style(f"=======================================================\n", fg="cyan"))

    try:
        runner = ScenarioRunner.from_directory(
            target,
            live=live,
            hyperscaler=hyperscaler,
            judge_samples=judge_samples,
        )
    except Exception as e:
        click.echo(click.style(f"Configuration error: {e}", fg="red"), err=True)
        sys.exit(1)

    click.echo(f"Loaded {len(runner.scenarios)} test scenarios.")
    click.echo(f"Agent ID: {runner.agent_config.get('agent_id', 'unknown')}")
    click.echo(f"Policy ID: {runner.policy.policy_id}")
    click.echo("Running assurance pipeline...\n")

    receipt = runner.run_all(output_dir=output)

    summary = receipt["summary"]
    verdict = receipt["verdict"]

    # Print scenario table
    click.echo("Scenario Breakdown:")
    click.echo("-" * 75)
    for s in receipt["scenarios"]:
        v_color = "green" if s["verdict"] == "PASS" else ("yellow" if s["verdict"] == "REVIEW" else "red")
        click.echo(
            f" * [{click.style(s['verdict'], fg=v_color, bold=True):<6}] "
            f"{s['scenario_id']:<24} "
            f"Cost: ${s['finops']['cost_usd']:.5f} | "
            f"Lat: {s['finops']['latency_ms']}ms | "
            f"Quality: {s['judge_evaluation']['score'] if s['judge_evaluation'] else 'N/A'}"
        )
        if s.get("policy_violations"):
            for v in s["policy_violations"]:
                click.echo(f"     |-> Policy Gate: {click.style(v, fg='red')}")

    click.echo("-" * 75)
    click.echo("\nAssurance & FinOps Summary:")
    click.echo(f" * Scenarios Passed: {summary['passed_scenarios']} / {summary['total_scenarios']}")
    click.echo(f" * Mean Quality Score: {summary['mean_quality_score']} / 5.0")
    click.echo(f" * Total Tokens: {summary['total_tokens']} (Prompt: {summary['prompt_tokens']}, Comp: {summary['completion_tokens']})")
    click.echo(f" * Total Cost: ${summary['total_cost_usd']:.6f} USD")
    click.echo(f" * Cost Per Successful Task: ${summary['cost_per_successful_task_usd']:.6f} USD")
    click.echo(f" * Total Retries: {summary['total_retries']}")
    click.echo(f" * Mean Latency: {summary['mean_latency_ms']:.1f} ms")

    # Digital Verification & Audit Trail
    click.echo("\nAudit-Ready Verification Trail:")
    click.echo(f" * Algorithm: {receipt['integrity']['algorithm']}")
    click.echo(f" * Tamper-Evident SHA-256 Receipt: {receipt['integrity']['canonical_hash']}")

    # Location of outputs
    if "artifacts" in receipt:
        json_p = Path(receipt["artifacts"]["json_path"])
        html_p = Path(receipt["artifacts"]["html_path"])
        json_size = json_p.stat().st_size if json_p.exists() else 0
        html_size = html_p.stat().st_size if html_p.exists() else 0

        click.echo(f"\nAudit Artifacts Saved:")
        click.echo(f" * Structured JSON Receipt : {json_p} ({json_size} bytes)")
        click.echo(f" * Interactive HTML Report : {html_p} ({html_size} bytes)")

        if open_report and html_p.exists():
            click.echo(f" Opening HTML report in web browser: {html_p}")
            webbrowser.open(html_p.as_uri())

    # Final Verdict Display
    color = "green" if verdict == "PASS" else ("yellow" if verdict == "REVIEW" else "red")
    click.echo("\n" + "=" * 55)
    click.echo(f" FINAL ASSURANCE VERDICT: {click.style(verdict, fg=color, bold=True)}")
    click.echo("=" * 55 + "\n")

    exit_code = PolicyEngine.get_exit_code(EvaluationVerdict(verdict), strict=strict)
    if exit_code != 0:
        click.echo(click.style(f"Exiting with status code {exit_code} due to policy failures.", fg="red"), err=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
