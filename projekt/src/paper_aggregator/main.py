"""Entry point for the paper-aggregator CLI."""

from paper_aggregator.cli.commands import app


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
