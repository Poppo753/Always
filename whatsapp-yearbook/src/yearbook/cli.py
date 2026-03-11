from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from yearbook.constants import PIPELINE_STAGES

app = typer.Typer(
    name="yearbook",
    help="WhatsApp Daily Yearbook Generator",
    add_completion=False,
)
console = Console()

_DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def _get_orchestrator(
    project_root: Path,
    run_id: str,
    force: bool,
):
    from yearbook.pipeline.orchestrator import PipelineOrchestrator
    return PipelineOrchestrator(project_root=project_root, run_id=run_id, force_rerun=force)


@app.command("run-all")
def run_all(
    project_root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root dir"),
    run_id: str = typer.Option("default", "--run-id", help="Run identifier"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-run all stages"),
) -> None:
    """Run the full pipeline from bootstrap to render."""
    root = project_root or _DEFAULT_ROOT
    orch = _get_orchestrator(root, run_id, force)
    orch.run_all()
    console.print(f"[bold green]Done![/bold green] PPTX saved to: {orch.paths.pptx_output}")


@app.command("run-stage")
def run_stage(
    stage: str = typer.Argument(help=f"Stage name: {', '.join(PIPELINE_STAGES)}"),
    project_root: Optional[Path] = typer.Option(None, "--root", "-r"),
    run_id: str = typer.Option("default", "--run-id"),
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    """Run a single pipeline stage."""
    if stage not in PIPELINE_STAGES:
        console.print(f"[red]Unknown stage '{stage}'. Valid: {', '.join(PIPELINE_STAGES)}[/red]")
        raise typer.Exit(1)
    root = project_root or _DEFAULT_ROOT
    orch = _get_orchestrator(root, run_id, force)
    orch.run_stage(stage)
    console.print(f"[green]Stage '{stage}' complete.[/green]")


@app.command("resume")
def resume(
    from_stage: str = typer.Argument(help="Resume from this stage"),
    project_root: Optional[Path] = typer.Option(None, "--root", "-r"),
    run_id: str = typer.Option("default", "--run-id"),
) -> None:
    """Resume pipeline from a given stage (re-runs that stage and all after it)."""
    if from_stage not in PIPELINE_STAGES:
        console.print(f"[red]Unknown stage '{from_stage}'.[/red]")
        raise typer.Exit(1)
    root = project_root or _DEFAULT_ROOT
    orch = _get_orchestrator(root, run_id, False)
    orch.resume_from(from_stage)
    console.print(f"[green]Resumed from '{from_stage}' — pipeline complete.[/green]")


@app.command("list-stages")
def list_stages() -> None:
    """List all pipeline stages in order."""
    for i, stage in enumerate(PIPELINE_STAGES, 1):
        console.print(f"  {i:2}. {stage}")


@app.command("status")
def status(
    project_root: Optional[Path] = typer.Option(None, "--root", "-r"),
    run_id: str = typer.Option("default", "--run-id"),
) -> None:
    """Show completion status of all stages for a run."""
    root = project_root or _DEFAULT_ROOT
    from yearbook.paths import ProjectPaths
    from yearbook.storage.manifest_store import ManifestStore

    paths = ProjectPaths(root, run_id)
    if not paths.run_manifest.exists():
        console.print(f"[yellow]No manifest found for run '{run_id}'.[/yellow]")
        raise typer.Exit(1)

    ms = ManifestStore(paths.run_manifest)
    manifest = ms.read()
    done = set(manifest.completed_stages) if manifest else set()

    for stage in PIPELINE_STAGES:
        tick = "[green]✓[/green]" if stage in done else "[dim]○[/dim]"
        console.print(f"  {tick}  {stage}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
