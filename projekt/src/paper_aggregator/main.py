"""Entry point for the paper-aggregator CLI."""

from paper_aggregator.cli.commands import app
from paper_aggregator.config.settings import settings
from paper_aggregator.db.repository import PaperRepository


def main() -> None:
    db = PaperRepository(settings.db_path)
    db.initialize()

    """Run the CLI application."""
    # app()


if __name__ == "__main__":
    main()
