"""AgentGuard CLI interface."""

from __future__ import annotations
import sys
from pathlib import Path
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
@click.option("--output-dir", "-o", default="reports", help="Directory to save evidence receipts and HTML report.")
@click.option("--strict", is_flag=True, default=False, help="Fail with non-zero exit code on REVIEW status.")
def evaluate(target_path: str, output_dir: str, strict: bool) -> None:
    """Evaluate an AI agent scenario directory against assurance policies."""
    logger = get_redacting_logger("agentguard.cli")
    target = Path(target_path)
    output = Path(output_dir)

    click.echo(click.style(f"\n=======================================================", fg="cyan"))
    click.echo(click.style(f" AgentGuard Assurance Evaluation Pipeline ", fg="cyan", bold=True))
    click.echo(click.style(f" Target: {target.resolve()}", fg="cyan"))
    click.echo(click.style(f"=======================================================\n", fg="cyan"))

    try:
        runner = ScenarioRunner.from_directory(target)
    except Exception as e:
        click.echo(click.style(f"Configuration error: {e}", fg="red"), err=True)
        sys.exit(1)

    click.echo(f"Loaded {len(runner.scenarios)} synthetic test scenarios.")
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
            f"{s['scenario_id']:<20} "
            f"Cost: ${s['finops']['cost_usd']:.5f} | "
            f"Lat: {s['finops']['latency_ms']}ms | "
            f"Quality: {s['judge_evaluation']['score'] if s['judge_evaluation'] else 'N/A'}"
        )
        if s.get("policy_violations"):
            for v in s["policy_violations"]:
                click.echo(f"     |-> Violation: {click.style(v, fg='red')}")

    click.echo("-" * 75)
    click.echo("\nAssurance & FinOps Summary:")
    click.echo(f" * Scenarios Passed: {summary['passed_scenarios']} / {summary['total_scenarios']}")
    click.echo(f" * Mean Quality Score: {summary['mean_quality_score']} / 5.0")
    click.echo(f" * Total Tokens: {summary['total_tokens']} (Prompt: {summary['prompt_tokens']}, Comp: {summary['completion_tokens']})")
    click.echo(f" * Total Cost: ${summary['total_cost_usd']:.6f} USD")
    click.echo(f" * Cost Per Successful Task: ${summary['cost_per_successful_task_usd']:.6f} USD")
    click.echo(f" * Total Retries: {summary['total_retries']}")
    click.echo(f" * Mean Latency: {summary['mean_latency_ms']:.1f} ms")

    # Cryptographic integrity
    click.echo("\nCryptographic Provenance:")
    click.echo(f" * Algorithm: {receipt['integrity']['algorithm']}")
    click.echo(f" * Canonical SHA-256: {receipt['integrity']['canonical_hash']}")

    if "artifacts" in receipt:
        click.echo(f"\nArtifacts Generated:")
        click.echo(f" * JSON Receipt: {receipt['artifacts']['json_path']}")
        click.echo(f" * HTML Report:  {receipt['artifacts']['html_path']}")

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
