"""CLI command definitions using Typer."""

import typer

app = typer.Typer(
    name="paper-aggregator",
    help="Build a personal, searchable research-paper library with LLM-assisted tagging.",
)


@app.command()
def add(
    urls: list[str] = typer.Argument(..., help="One or more URLs to papers."),
    force: bool = typer.Option(False, "--force", help="Re-ingest an already-known URL."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print tags without writing to DB."),
    model: str | None = typer.Option(None, "--model", help="Override the default LLM model."),
) -> None:
    """Download and tag papers from URLs."""
    ...


@app.command()
def search(
    tag: list[str] = typer.Option([], "--tag", help="Filter by tag (AND semantics, repeatable)."),
    author: str | None = typer.Option(None, "--author", help="Filter by author (substring match)."),
    field: str | None = typer.Option(None, "--field", help="Filter by primary_field or sub_field."),
    year: str | None = typer.Option(None, "--year", help="Filter by year (YYYY or YYYY-YYYY)."),
    limit: int = typer.Option(50, "--limit", "-n", help="Cap results."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON."),
) -> None:
    """Search papers by tags, author, field, or year."""
    ...


@app.command()
def list_papers(
    tag: str | None = typer.Option(None, "--tag", help="Filter by a specific tag."),
    limit: int = typer.Option(50, "--limit", "-n", help="Cap results."),
) -> None:
    """List all papers in the database, newest first."""
    ...


@app.command()
def show(id_or_url: str = typer.Argument(..., help="Paper ID or URL to display.")) -> None:
    """Show full details for a single paper."""
    ...


@app.command()
def remove(id_or_url: str = typer.Argument(..., help="Paper ID or URL to delete.")) -> None:
    """Remove a paper and its tags from the database."""
    ...


@app.command()
def tags() -> None:
    """List all distinct tags in the database with paper counts."""
    ...


@app.command()
def init() -> None:
    """Scaffold a default config file interactively."""
    ...


@app.command()
def config(
    key: str | None = typer.Option(None, "--key", help="Config key to read or set."),
    value: str | None = typer.Option(None, "--value", help="Value to set for the given key."),
) -> None:
    """Read or set configuration values."""
    ...
