"""Entry point for the paper-aggregator CLI."""

from paper_aggregator.cli.commands import app
from paper_aggregator.config.settings import settings
from paper_aggregator.db.repository import PaperRepository


def main() -> None:
    """Run the CLI application."""
    db = PaperRepository(settings.db_path)
    db.initialize()

    # Make the database and settings available to CLI command handlers
    # via the Typer context so they don't need to import the module-level
    # singleton directly.
    app.context_settings = {"obj": {"db": db, "settings": settings}}
    app()


if __name__ == "__main__":
    main()
