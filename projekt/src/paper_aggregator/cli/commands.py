"""CLI command definitions using Typer."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from paper_aggregator.config.settings import settings as app_settings
from paper_aggregator.db.repository import PaperRepository
from paper_aggregator.domain.ingestor import (
    compute_content_hash,
    detect_file_type,
    download_pdf,
    extract_text,
    validate_url,
)
from paper_aggregator.domain.models import PaperTags
from paper_aggregator.domain.search import build_search_filters
from paper_aggregator.domain.tagger import tag_paper, truncate_text

app = typer.Typer(
    name="paper-aggregator",
    help="Build a personal, searchable research-paper library with LLM-assisted tagging.",
)

console = Console()


def _get_db() -> PaperRepository:
    """Return a database repository instance."""
    db = PaperRepository(app_settings.db_path)
    db.initialize()
    return db


def _get_settings():
    """Return the global settings instance."""
    return app_settings


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------
@app.command()
def add(
    urls: list[str] = typer.Argument(..., help="One or more URLs to papers."),
    force: bool = typer.Option(False, "--force", help="Re-ingest an already-known URL."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print tags without writing to DB."),
    model: str | None = typer.Option(None, "--model", help="Override the default LLM model."),
) -> None:
    """Download and tag papers from URLs."""
    db: PaperRepository = _get_db()
    settings = _get_settings()
    pdf_dir = settings.pdf_storage_path
    pdf_dir.mkdir(parents=True, exist_ok=True)

    for url in urls:
        console.print(f"\n[bold]Processing:[/bold] {url}")

        # ── 1. Determine source: local file or remote URL ──────────────────
        local_path: Path | None = None
        if Path(url).is_file():
            local_path = Path(url).resolve()
            # Use a file:// URI as the canonical "url" for dedup purposes.
            db_url = local_path.as_uri()
            console.print(f"  [dim]Local file: {local_path}[/dim]")
        elif not validate_url(url):
            console.print(f"  [red]✗[/red] Invalid URL or non-existent file: {url}")
            continue
        else:
            db_url = url

        # ── 2. Check for duplicates ────────────────────────────────────────
        if db.paper_exists(db_url):
            if force:
                console.print("  [yellow]⚠[/yellow] Already ingested — re-ingesting (--force).")
                db.remove_paper_by_url(db_url)
            else:
                console.print("  [yellow]⚠[/yellow] Already ingested. Use --force to re-ingest.")
                continue

        # ── 3. Obtain the file (download or use local) ──────────────────────
        if local_path is not None:
            tmp_path = local_path
            content_type = None
            try:
                content_hash = compute_content_hash(local_path)
                console.print(f"  [green]✓[/green] Using local file ({content_hash[:8]}…)")
            except PermissionError:
                console.print(
                    f"  [red]✗[/red] Permission denied: {local_path}\n"
                    "  [dim]macOS blocks Python from reading files in "
                    "~/Downloads, ~/Desktop, and ~/Documents.\n"
                    "  Workaround: move the file somewhere else first —\n"
                    f"    [bold]mv '{local_path}' /tmp/in.pdf && "
                    f"paper-aggregator add /tmp/in.pdf[/bold][/dim]"
                )
                continue
        else:
            try:
                tmp_path = Path(pdf_dir) / f"_tmp_{url.split('/')[-1] or 'paper'}"
                content_hash, content_type = download_pdf(db_url, tmp_path)
                console.print(f"  [green]✓[/green] Downloaded ({content_hash[:8]}…)")
            except Exception as exc:
                console.print(f"  [red]✗[/red] Download failed: {exc}")
                continue

        # ── 4. Detect file type and extract text ───────────────────────────
        try:
            file_type = detect_file_type(content_type, db_url)
        except ValueError as exc:
            console.print(f"  [red]✗[/red] {exc}")
            if not local_path:
                tmp_path.unlink(missing_ok=True)
            continue

        try:
            if file_type == "pdf":
                text = extract_text(tmp_path)
            else:
                text = tmp_path.read_text(encoding="utf-8")
        except (ValueError, OSError) as exc:
            console.print(f"  [red]✗[/red] Text extraction failed: {exc}")
            if not local_path:
                tmp_path.unlink(missing_ok=True)
            continue

        if not text.strip():
            console.print("  [red]✗[/red] No text could be extracted.")
            if not local_path:
                tmp_path.unlink(missing_ok=True)
            continue

        console.print(f"  [green]✓[/green] Extracted {len(text)} characters.")

        # ── 5. Truncate and tag ────────────────────────────────────────────
        truncated, was_truncated = truncate_text(text, settings.max_context_chars)
        if was_truncated:
            console.print(
                f"  [yellow]⚠[/yellow] Text truncated to "
                f"{settings.max_context_chars} characters."
            )

        try:
            tags: PaperTags = tag_paper(truncated, model=model)
        except ValueError as exc:
            console.print(f"  [red]✗[/red] LLM tagging failed: {exc}")
            if not local_path:
                tmp_path.unlink(missing_ok=True)
            continue

        console.print(f"  [green]✓[/green] Tagged — title: {tags.title!r}")

        if dry_run:
            console.print_json(tags.model_dump_json())
            if not local_path:
                tmp_path.unlink(missing_ok=True)
            continue

        # ── 6. Store in DB ─────────────────────────────────────────────────
        try:
            paper_id = db.add_paper(
                db_url,
                str(tmp_path) if local_path else str(tmp_path),
                content_hash,
            )
            db.save_paper_metadata(
                paper_id=paper_id,
                title=tags.title,
                authors=tags.authors,
                year=tags.year,
                primary_field=tags.primary_field,
                sub_field=tags.sub_field,
                keywords=tags.keywords,
                methodology=tags.methodology,
                abstract_summary=tags.abstract_summary,
            )
            console.print(f"  [green]✓[/green] Stored in database (ID: {paper_id}).")
        except Exception as exc:
            console.print(f"  [red]✗[/red] Database write failed: {exc}")
            if not local_path:
                tmp_path.unlink(missing_ok=True)
            continue

        # ── 7. Store PDF in the library folder ─────────────────────────────
        if local_path:
            # Copy local file into the managed pdfs/ directory.
            final_path = pdf_dir / f"{paper_id}.pdf"
            shutil.copy2(local_path, final_path)
            console.print(f"  [green]✓[/green] PDF copied to {final_path}")
        else:
            final_path = pdf_dir / f"{paper_id}.pdf"
            tmp_path.rename(final_path)
            console.print(f"  [green]✓[/green] PDF stored at {final_path}")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------
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
    db: PaperRepository = _get_db()
    filters = build_search_filters(
        tags=tag if tag else None,
        author=author,
        field=field,
        year=year,
        limit=limit,
    )

    results = db.search_papers(
        tags=filters.tags,
        author=filters.author,
        field=filters.field,
        year=year,
        limit=filters.limit,
    )

    if not results:
        console.print("[dim]No papers matched your query.[/dim]")
        raise typer.Exit()

    if json_output:
        print(json.dumps(results, indent=2))
        return

    _render_paper_table(results)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------
@app.command()
def list_papers(
    tag: str | None = typer.Option(None, "--tag", help="Filter by a specific tag."),
    limit: int = typer.Option(50, "--limit", "-n", help="Cap results."),
) -> None:
    """List all papers in the database, newest first."""
    db: PaperRepository = _get_db()
    results = db.list_all(tag=tag, limit=limit)

    if not results:
        console.print("[dim]No papers in the database.[/dim]")
        raise typer.Exit()

    _render_paper_table(results)


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------
@app.command()
def show(id_or_url: str = typer.Argument(..., help="Paper ID or URL to display.")) -> None:
    """Show full details for a single paper."""
    db: PaperRepository = _get_db()

    paper = None
    if id_or_url.isdigit():
        paper = db.get_paper(int(id_or_url))
    else:
        paper = db.get_paper_by_url(id_or_url)

    if paper is None:
        console.print(f"[red]No paper found for:[/red] {id_or_url}")
        raise typer.Exit(code=1)

    console.print(f"[bold]Title:[/bold] {paper.get('title', 'N/A')}")
    console.print(f"[bold]ID:[/bold] {paper['id']}")
    console.print(f"[bold]URL:[/bold] {paper['url']}")
    console.print(f"[bold]Authors:[/bold] {paper.get('authors', 'N/A')}")
    console.print(f"[bold]Year:[/bold] {paper.get('year', 'N/A')}")
    console.print(f"[bold]Field:[/bold] {paper.get('primary_field', 'N/A')}"
                  f" / {paper.get('sub_field', 'N/A')}")
    console.print(f"[bold]Keywords:[/bold] {paper.get('keywords', 'N/A')}")
    console.print(f"[bold]Methodology:[/bold] {paper.get('methodology', 'N/A')}")
    console.print(f"[bold]Abstract:[/bold] {paper.get('abstract_summary', 'N/A')}")
    console.print(f"[bold]File:[/bold] {paper.get('file_path', 'N/A')}")
    console.print(f"[bold]Ingested at:[/bold] {paper.get('ingested_at', 'N/A')}")


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------
@app.command()
def remove(id_or_url: str = typer.Argument(..., help="Paper ID or URL to delete.")) -> None:
    """Remove a paper and its tags from the database."""
    db: PaperRepository = _get_db()

    if id_or_url.isdigit():
        deleted = db.remove_paper(int(id_or_url))
    else:
        deleted = db.remove_paper_by_url(id_or_url)

    if deleted:
        console.print(f"[green]✓[/green] Removed: {id_or_url}")
    else:
        console.print(f"[red]No paper found for:[/red] {id_or_url}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# tags
# ---------------------------------------------------------------------------
@app.command()
def tags() -> None:
    """List all distinct tags in the database with paper counts."""
    db: PaperRepository = _get_db()
    rows = db.list_tags()

    if not rows:
        console.print("[dim]No tags in the database.[/dim]")
        raise typer.Exit()

    table = Table(title="Tags")
    table.add_column("Tag", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Papers", justify="right")

    for row in rows:
        table.add_row(row["name"], row["category"], str(row["paper_count"]))

    console.print(table)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------
@app.command()
def init() -> None:
    """Scaffold a default config file interactively."""
    from paper_aggregator.config.settings import _default_config_path

    config_path = _default_config_path()
    if config_path.exists():
        overwrite = typer.confirm(
            f"Config already exists at {config_path}. Overwrite?"
        )
        if not overwrite:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit()

    api_base_url = typer.prompt(
        "API base URL", default="https://api.openai.com/v1"
    )
    model = typer.prompt("Default model", default="gpt-4o-mini")
    max_chars = typer.prompt(
        "Max context characters", default=6000, type=int
    )

    config_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# paper-aggregator configuration
# Environment variable PAPER_AGGREGATOR_API_KEY takes precedence for the API key.

api_base_url = "{api_base_url}"
model = "{model}"
max_context_chars = {max_chars}
"""
    config_path.write_text(content)
    console.print(f"[green]✓[/green] Config written to {config_path}")


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
@app.command()
def config(
    key: str | None = typer.Option(None, "--key", help="Config key to read or set."),
    value: str | None = typer.Option(None, "--value", help="Value to set for the given key."),
) -> None:
    """Read or set configuration values."""
    from paper_aggregator.config.settings import _default_config_path

    import tomli_w

    config_path = _default_config_path()

    # Read mode: show all or a specific key.
    if value is None:
        if key:
            # Show one key.
            settings = _get_settings()
            val = getattr(settings, key, None)
            if val is None:
                console.print(f"[red]Unknown config key:[/red] {key}")
                raise typer.Exit(code=1)
            console.print(f"{key} = {val}")
        else:
            # Show all settings.
            if config_path.exists():
                console.print(config_path.read_text())
            else:
                console.print(
                    f"[dim]No config file at {config_path}. "
                    f"Run [bold]paper-aggregator init[/bold] to create one.[/dim]"
                )
        return

    # Write mode: set a key.
    if key is None:
        console.print("[red]Provide --key when using --value.[/red]")
        raise typer.Exit(code=1)

    allowed_keys = {"api_base_url", "model", "max_context_chars", "db_path", "pdf_storage_path"}
    if key not in allowed_keys:
        console.print(f"[red]Unknown config key:[/red] {key}. Allowed: {', '.join(sorted(allowed_keys))}")
        raise typer.Exit(code=1)

    # Cast value to int if needed.
    typed_value: str | int = value
    if key == "max_context_chars":
        try:
            typed_value = int(value)
        except ValueError:
            console.print(f"[red]max_context_chars must be an integer, got:[/red] {value}")
            raise typer.Exit(code=1)

    # Load existing or start fresh.
    if config_path.exists():
        import tomllib
        data = tomllib.loads(config_path.read_text())
    else:
        data = {}

    data[key] = typed_value
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(tomli_w.dumps(data))
    console.print(f"[green]✓[/green] Set {key} = {typed_value}")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _render_paper_table(results: list[dict]) -> None:
    """Render a list of paper dicts as a Rich table."""
    table = Table(title=f"Papers ({len(results)})")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Authors")
    table.add_column("Year", justify="right")
    table.add_column("Keywords")

    for row in results:
        table.add_row(
            str(row["id"]),
            row.get("title", "N/A") or "N/A",
            row.get("authors", "") or "",
            str(row.get("year") or ""),
            row.get("keywords", "") or "",
        )

    console.print(table)
