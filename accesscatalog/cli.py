"""AccessCatalog Agent CLI."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="accesscatalog",
    help="DataHub-powered accessibility compliance agent for document catalogs.",
    no_args_is_help=True,
)
console = Console()

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Minimal .env loader (KEY=VALUE lines, no quoting games)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@app.command()
def ingest(
    server: str = typer.Option("http://localhost:8080", help="DataHub GMS URL"),
    manifest: Path = typer.Option(REPO_ROOT / "corpus/manifest.yaml"),
) -> None:
    """Register the document corpus in DataHub (unscanned baseline)."""
    from accesscatalog.ingest import bootstrap_catalog, get_graph, load_manifest

    data = load_manifest(manifest)
    urns = bootstrap_catalog(get_graph(server), data)
    console.print(
        f"[green]Ingested {len(urns)} documents[/green] across "
        f"{len(data['departments'])} departments into {server}"
    )
    console.print("All documents tagged [bold]unscanned[/bold] — run the agent next.")


@app.command()
def scan(pdf: Path) -> None:
    """Scan a single PDF locally (no DataHub write) and print the results."""
    from accesscatalog.scanner import scan as run_scan

    result = run_scan(pdf)
    table = Table(title=f"{pdf.name} — score {result.score}/100")
    table.add_column("Check")
    table.add_column("Severity")
    table.add_column("Result")
    table.add_column("Detail", max_width=60)
    for c in result.checks:
        table.add_row(
            c.name,
            c.severity,
            "[green]pass[/green]" if c.passed else "[red]FAIL[/red]",
            c.detail,
        )
    console.print(table)
    verdict = "COMPLIANT" if result.compliant else "NON-COMPLIANT"
    color = "green" if result.compliant else "red"
    console.print(f"Verdict: [{color} bold]{verdict}[/{color} bold]")


@app.command()
def agent(
    server: str = typer.Option("http://localhost:8080", help="DataHub GMS URL"),
    model: str = typer.Option(None, help="OpenAI model (default: $ACCESSCATALOG_MODEL or gpt-5.1)"),
) -> None:
    """Run the compliance agent: scan, write back, build the remediation queue."""
    _load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]OPENAI_API_KEY is not set.[/red] Add it to .env or export it.")
        raise typer.Exit(1)

    from accesscatalog.agent.runner import run_agent

    console.print("[bold]AccessCatalog Agent[/bold] — starting compliance pass…")
    outcome = asyncio.run(run_agent(server_url=server, model=model))
    console.print(
        f"\n[green]Done.[/green] Scanned {outcome['scanned']} documents, "
        f"queued {outcome['queued']} for remediation."
    )
    console.print(f"Queue:   {outcome['queue_file']}")
    console.print(f"Summary: {outcome['summary_file']}\n")
    console.print(outcome["final_output"])


@app.command()
def report(
    server: str = typer.Option("http://localhost:8080", help="DataHub GMS URL"),
    out: Path = typer.Option(REPO_ROOT / "reports"),
) -> None:
    """Generate compliance reports from live catalog state."""
    from accesscatalog.report.generator import generate_reports

    paths = generate_reports(server, out)
    for p in paths:
        console.print(f"[green]wrote[/green] {p}")


@app.command()
def status(
    server: str = typer.Option("http://localhost:8080", help="DataHub GMS URL"),
) -> None:
    """Quick compliance posture summary read from the live catalog."""
    from accesscatalog.report.generator import collect_catalog_state

    state = collect_catalog_state(server)
    table = Table(title=f"{state['municipality']} — document compliance")
    table.add_column("Department")
    table.add_column("Docs", justify="right")
    table.add_column("Compliant", justify="right")
    table.add_column("Non-compliant", justify="right")
    table.add_column("In remediation", justify="right")
    table.add_column("Unscanned", justify="right")
    for dept, row in state["departments"].items():
        table.add_row(
            dept,
            str(row["total"]),
            f"[green]{row['compliant']}[/green]",
            f"[red]{row['non_compliant']}[/red]",
            f"[yellow]{row['in_remediation']}[/yellow]",
            str(row["unscanned"]),
        )
    console.print(table)


if __name__ == "__main__":
    app()
