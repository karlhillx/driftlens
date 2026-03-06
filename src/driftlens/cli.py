from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .engine import compare_snapshots
from .loaders import load_snapshot
from .models import Severity
from .policy import load_policy
from .reporting import redact_value, severity_ge, to_junit_xml

app = typer.Typer(help="Detect risky config drift between environments.")
console = Console()


@app.command()
def scan(
    baseline: Annotated[Path, typer.Option("--baseline", exists=True, file_okay=False, dir_okay=True, readable=True)],
    target: Annotated[Path, typer.Option("--target", exists=True, file_okay=False, dir_okay=True, readable=True)],
    format: Annotated[str, typer.Option("--format", help="table|markdown|json")] = "table",
    policy: Annotated[
        Path | None,
        typer.Option("--policy", exists=True, file_okay=True, dir_okay=False, readable=True, help="Policy file (.driftlens.yaml)"),
    ] = None,
    fail_on: Annotated[Severity, typer.Option("--fail-on", help="Fail CI when severity >= threshold")] = Severity.CRITICAL,
    show_values: Annotated[bool, typer.Option("--show-values", help="Show raw config values (default is redacted)")] = False,
    junit_out: Annotated[Path | None, typer.Option("--junit-out", help="Write JUnit XML report to this file")] = None,
) -> None:
    baseline_data = load_snapshot(baseline)
    target_data = load_snapshot(target)
    active_policy = load_policy(policy, baseline=baseline, target=target)

    result = compare_snapshots(
        baseline_name=str(baseline),
        target_name=str(target),
        baseline=baseline_data,
        target=target_data,
        policy=active_policy,
    )

    if junit_out:
        junit_out.parent.mkdir(parents=True, exist_ok=True)
        junit_out.write_text(to_junit_xml(result, fail_on=fail_on), encoding="utf-8")

    fmt = format.lower().strip()
    if fmt == "json":
        payload = result.model_dump(mode="json")
        if not show_values:
            for item in payload["items"]:
                item["baseline_value"] = redact_value(item.get("baseline_value"), show_values=False)
                item["target_value"] = redact_value(item.get("target_value"), show_values=False)
        payload["fail_on"] = fail_on.value
        payload["failed"] = any(severity_ge(Severity(i["severity"]), fail_on) for i in payload["items"])
        console.print_json(json.dumps(payload))
    elif fmt == "markdown":
        typer.echo("# DriftLens Report\n")
        typer.echo(f"- Baseline: `{result.baseline}`")
        typer.echo(f"- Target: `{result.target}`")
        typer.echo(f"- Total drift items: **{result.total}**")
        typer.echo(f"- Fail threshold: **{fail_on.value}**")
        typer.echo(
            f"- Severity: critical={result.by_severity['critical']}, high={result.by_severity['high']}, "
            f"medium={result.by_severity['medium']}, low={result.by_severity['low']}\n"
        )
        typer.echo("| Severity | Change | Key | Baseline | Target |")
        typer.echo("|---|---|---|---|---|")
        for item in result.items:
            b = redact_value(item.baseline_value, show_values=show_values).replace("|", "\\|")
            t = redact_value(item.target_value, show_values=show_values).replace("|", "\\|")
            typer.echo(f"| {item.severity.value} | {item.change_type} | `{item.key}` | `{b}` | `{t}` |")
    else:
        table = Table(title="DriftLens Report")
        table.add_column("Severity", style="bold")
        table.add_column("Change")
        table.add_column("Key")
        table.add_column("Baseline")
        table.add_column("Target")

        for item in result.items:
            table.add_row(
                item.severity.value.upper(),
                item.change_type,
                item.key,
                redact_value(item.baseline_value, show_values=show_values),
                redact_value(item.target_value, show_values=show_values),
            )

        console.print(
            f"[bold]Baseline:[/bold] {result.baseline}  [bold]Target:[/bold] {result.target}  "
            f"[bold]Total:[/bold] {result.total}  [bold]Fail-on:[/bold] {fail_on.value}"
        )
        console.print(
            f"critical={result.by_severity['critical']} high={result.by_severity['high']} "
            f"medium={result.by_severity['medium']} low={result.by_severity['low']}"
        )
        console.print(table)

    should_fail = any(severity_ge(item.severity, fail_on) for item in result.items)
    if should_fail:
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
