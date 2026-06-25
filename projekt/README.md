# Paper Aggregator

A single-user CLI tool that builds a personal, searchable research-paper library. Feed it paper URLs (PDFs or arXiv links), and it downloads, extracts text, and sends it to an LLM for structured tagging. Tagged metadata lands in a local SQLite database - searchable offline anytime.

## Features

- **Ingest papers** from URLs - downloads, extracts text via PyMuPDF, tags with an LLM
- **LLM tagging** - structured metadata: title, authors, year, field, keywords, methodology, summary
- **Offline search** - filter by tags, author, field, or year; no internet needed after ingestion
- **Library management** - list, show, remove papers; browse all tags
- **BibTeX export** - generate citation entries for any paper in the library
- **Multiple LLM backends** - works with OpenAI, Ollama, LiteLLM, or any OpenAI-compatible API

## Project Structure

```
paper-aggregator/
├── src/paper_aggregator/
│   ├── main.py                  # CLI entry point
│   ├── cli/
│   │   └── commands.py          # Typer commands (add, search, list, show, …)
│   ├── config/
│   │   └── settings.py          # Config loading (TOML + env vars)
│   ├── db/
│   │   └── repository.py        # SQLite data access (Repository pattern)
│   └── domain/
│       ├── ingestor.py          # URL validation, download, PDF extraction
│       ├── tagger.py            # LLM tagging (OpenAI-compatible API)
│       ├── search.py            # Search filter parsing and query building
│       ├── bibtex.py            # BibTeX citation formatting
│       └── models.py            # Pydantic schemas (PaperTags, …)
├── tests/                       # pytest test suite
├── config.toml                  # Sample configuration file
├── Dockerfile                   # Docker build
├── pyproject.toml               # Build & dependency declarations
├── REQUIREMENTS.md              # Full requirements & implementation status
└── README.md
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `httpx` | Download files from URLs |
| `pymupdf` (fitz) | PDF text extraction |
| `openai` | LLM API client (OpenAI-compatible) |
| `pydantic` | Schema validation for LLM responses |
| `rich` | Pretty-printed CLI tables |
| `typer` | CLI argument parsing |
| `tomli` / `tomli-w` | Config file read/write |
| `python-dotenv` | .env file loading |
| `rapidfuzz` | Fuzzy author matching in search |

**Python ≥ 3.12** required.

## Installation

### pip (from source)

```bash
git clone <repo-url> && cd paper-aggregator
pip install .
```

### Poetry

```bash
git clone <repo-url> && cd paper-aggregator
poetry install --only main
```

### Docker

```bash
docker build -t paper-aggregator .
```

## Quick Start

### 1. Set your API key

```bash
export PAPER_AGGREGATOR_API_KEY="sk-..."
```

Or place it in a `.env` file in the project directory.

The tool works with any OpenAI-compatible endpoint - OpenAI, Ollama, LiteLLM, Mistral via proxy, etc.

### 2. (Optional) Initialize config

```bash
paper-aggregator init
```

This interactively prompts for `api_base_url`, `model`, and `max_context_chars`, then writes `~/.config/paper-aggregator/config.toml`.

### 3. Add a paper

```bash
paper-aggregator add https://arxiv.org/pdf/1706.03762.pdf
```

Use `--dry-run` to preview the LLM's tags without storing:

```bash
paper-aggregator add --dry-run https://arxiv.org/pdf/1706.03762.pdf
```

### 4. Search your library

```bash
# By tag
paper-aggregator search --tag transformers

# Multiple tags (AND)
paper-aggregator search --tag transformers --tag "attention mechanism"

# By author (fuzzy match)
paper-aggregator search --author Vaswani

# By field
paper-aggregator search --field "Natural Language Processing"

# By year or year range
paper-aggregator search --year 2017
paper-aggregator search --year 2017-2023

# JSON output
paper-aggregator search --tag nlp --json
```

### 5. Manage your library

```bash
paper-aggregator list                          # all papers, newest first
paper-aggregator list --tag nlp                # filter by tag
paper-aggregator show 1                        # full details for paper #1
paper-aggregator bibtex 1                      # BibTeX citation
paper-aggregator remove 1                      # delete paper #1
paper-aggregator tags                          # all tags with counts
```

### Docker usage

**Add this alias** to `~/.zshrc` (or `~/.bashrc`) - then Docker feels like a native install:

```bash
export PAPER_AGGREGATOR_API_KEY="<Your LLM API key>"
alias paper='docker run --rm -it \
  -e PAPER_AGGREGATOR_API_KEY \
  -v "${XDG_CONFIG_HOME:-$HOME/.config}/paper-aggregator:/config" \
  -v "${XDG_DATA_HOME:-$HOME/.local/share}/paper-aggregator:/data" \
  paper-aggregator'
```

Your host's `PAPER_AGGREGATOR_API_KEY` env var passes through automatically. After that:

```bash
paper init
paper add https://arxiv.org/pdf/1706.03762.pdf
paper search --tag transformers
paper list
```

**One-off commands** (if you don't want the alias):

```bash
docker run --rm -it -e PAPER_AGGREGATOR_API_KEY \
  -v "$HOME/.config/paper-aggregator:/config" \
  -v "$HOME/.local/share/paper-aggregator:/data" \
  paper-aggregator add https://arxiv.org/pdf/1706.03762.pdf
```

**Volumes:**
- `/config` - `config.toml` lives in its `paper-aggregator/` subdirectory
- `/data` - `papers.db` and `pdfs/` live in its `paper-aggregator/` subdirectory

## Configuration

### Environment variables

| Variable | Purpose |
|----------|---------|
| `PAPER_AGGREGATOR_API_KEY` | API key for the LLM provider (**required for `add`**) |
| `XDG_CONFIG_HOME` | Override config directory (default: `~/.config`) |
| `XDG_DATA_HOME` | Override data directory (default: `~/.local/share`) |

### Config file (`~/.config/paper-aggregator/config.toml`)

```toml
api_base_url = "https://api.openai.com/v1"   # OpenAI-compatible endpoint
model = "gpt-4o-mini"                        # Default LLM model
max_context_chars = 6000                     # Max text chars sent to LLM
# db_path = "/custom/path/papers.db"          # Override DB location
# pdf_storage_path = "/custom/path/pdfs"      # Override PDF storage
```

Environment variables take precedence over the config file.

## Running Tests

```bash
# All tests (unit)
pytest

# With coverage
pytest --cov=src/paper_aggregator --cov-report=term-missing

# Exclude integration tests (requires API key)
pytest --ignore=tests/test_integration.py
```

Tests use mocked LLM clients and HTTP downloads - no real network calls in unit tests.

## Architecture

The project follows a layered architecture:

```
CLI (Typer commands)
  └─► Command handlers (cli/commands.py)
        └─► Domain services (domain/*.py)
              └─► Repository (db/repository.py)
                    └─► SQLite
```

- **CLI layer** - argument parsing and output formatting only
- **Domain layer** - all business logic (ingestion, tagging, search, BibTeX)
- **Repository layer** - database access via Repository pattern
- **Config layer** - settings from TOML + env vars

All domain modules are callable without the CLI - designed for testability.

## Documentation

- **[REQUIREMENTS.md](REQUIREMENTS.md)** - Full requirements specification with implementation status
- Docstrings throughout the source for module/function-level documentation

## License

This is a personal/university project. PyMuPDF (fitz) is used under its AGPL license.
