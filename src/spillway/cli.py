from typing import Annotated

import typer
from rich.console import Console

from spillway.aws.filters import _build_filters
from spillway.config import load_configuration

app = typer.Typer()
console = Console()


@app.callback()
def main():
    """Spillway: AWS Security Hub to Jira Dispatcher"""
    pass


@app.command()
def triage(
    region: Annotated[
        str | None, typer.Option(help="AWS Region (Overrides config)")
    ] = None,
    severity: Annotated[
        list[str] | None, typer.Option(help="Filter by severity (Overrides config)")
    ] = None,
    config_file: Annotated[
        str | None, typer.Option(help="Explicit path to yaml config")
    ] = None,
):
    """Fetch Security Hub findings, apply filters, and process alerts."""

    config = load_configuration(
        explicit_file=config_file, cli_region=region, cli_severities=severity
    )
    console.print_json(data=_build_filters(config))
