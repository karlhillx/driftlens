from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .engine import compare_snapshots
from .loaders import load_snapshot

app = typer.Typer(help="Detect risky config drift between environments.")
console = Console()


@app.command()
def scan(
    baseline: Annotated[Path, typer.Option("--baseline", exists=True, file_okay=False, dir_okay=True, readable=True)],
    target: Annotated[Path, typer.Option("--target", exists=True, file_okay=False, dir_okay=True, readable=True)],
    format: Annotated[str, typer.Option("--format", help="table|markdown|json")] = "table",
    reveal: Annotated[bool, typer.Option("--reveal", help="Reveal critical secret values in output")] = False,
) -> None:
    baseline_data = load_snapshot(baseline)
    target_data = load_snapshot(target)

    result = compare_snapshots(
        baseline_name=str(baseline),
        target_name=str(target),
        baseline=baseline_data,
        target=target_data,
        reveal=reveal,
    )

    fmt = format.lower().strip()
    if fmt == "json":
        console.print_json(json.dumps(result.model_dump(mode="json")))
        return

    if fmt == "markdown":
        typer.echo(f"# DriftLens Report\n")
        typer.echo(f"- Baseline: `{result.baseline}`")
        typer.echo(f"- Target: `{result.target}`")
        typer.echo(f"- Total drift items: **{result.total}**")
        typer.echo(
            f"- Severity: critical={result.by_severity['critical']}, high={result.by_severity['high']}, "
            f"medium={result.by_severity['medium']}, low={result.by_severity['low']}\n"
        )
        typer.echo("| Severity | Change | Key | Baseline | Target |")
        typer.echo("|---|---|---|---|---|")
        for item in result.items:
            b = (item.baseline_value or "∅").replace("|", "\\|")
            t = (item.target_value or "∅").replace("|", "\\|")
            typer.echo(f"| {item.severity.value} | {item.change_type} | `{item.key}` | `{b}` | `{t}` |")
        return

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
            item.baseline_value or "∅",
            item.target_value or "∅",
        )

    console.print(
        f"[bold]Baseline:[/bold] {result.baseline}  [bold]Target:[/bold] {result.target}  "
        f"[bold]Total:[/bold] {result.total}"
    )
    console.print(
        f"critical={result.by_severity['critical']} high={result.by_severity['high']} "
        f"medium={result.by_severity['medium']} low={result.by_severity['low']}"
    )
    console.print(table)


if __name__ == "__main__":
    app()
