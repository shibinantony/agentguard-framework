"""CLI integration tests using Click CliRunner."""

from pathlib import Path
import pytest
from click.testing import CliRunner
from agentguard.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_evaluate_execution(tmp_path: Path):
    runner = CliRunner()
    out_dir = tmp_path / "cli_reports"
    
    # Run evaluation
    result = runner.invoke(
        main,
        ["evaluate", "examples/customer-support-agent", "--output-dir", str(out_dir)],
    )

    # Since the example contains intentional adversarial scenarios (cs-03 to cs-06),
    # the policy correctly issues a BLOCK verdict, which should yield exit code 1.
    assert result.exit_code == 1
    assert "FINAL ASSURANCE VERDICT: BLOCK" in result.output
    assert (out_dir / "evidence.json").exists()
    assert (out_dir / "evidence.html").exists()
