# LLM-Assisted Research Paper Aggregator - Requirements

## Overview

A single-user CLI tool that builds a personal, searchable research-paper library. The user feeds it URLs to papers (direct PDFs). The tool downloads each paper, extracts its text via PyMuPDF, and sends it to an OpenAI-compatible LLM for structured tagging. Tagged metadata lands in a local SQLite database; the source PDFs are stored in a local folder alongside it. Later, the user runs `search --tag <tag>` (or combinations of tag filters) to find papers by their assigned tags.

> **Status legend:** ✅ Implemented &nbsp;|&nbsp; ⚠️ Partial &nbsp;|&nbsp; ❌ Not yet implemented

---

## 1. Functional Requirements

### 1.1 Ingestion Pipeline (`add` command)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **F1.1** | Accept one or more URLs as arguments to `add`. | Must | ✅ |
| **F1.2** | Validate URLs before downloading (well-formed, reachable, HTTP 200). | Must | ✅ |
| **F1.3** | Download the remote file to a temporary location. | Must | ✅ |
| **F1.4** | Detect file type from Content-Type header or extension. | Must | ✅ |
| **F1.5** | Extract plain text from PDF files using **PyMuPDF** (fitz). | Must | ✅ |
| **F1.6** | Handle plain-text files (.txt) directly with no extraction step. | Could | ✅ |
| **F1.7** | Reject unsupported formats with a clear error message. | Must | ✅ |
| **F1.8** | Skip papers already present in the database (deduplication by URL or content hash). | Should | ⚠️ URL dedup only |
| **F1.9** | Accept a `--force` flag to re-ingest an already-known URL (overwrite existing tags). | Could | ⚠️ Not tested |
| **F1.10** | Copy the downloaded PDF to a local storage folder and record its path in the DB. | Must | ✅ |

### 1.2 LLM Tagging

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **F2.1** | Send extracted text (or first N characters/tokens) to the configured LLM for analysis. | Must | ✅ |
| **F2.2** | The LLM must return a **structured JSON object** with a fixed tagging schema (see §3). | Must | ✅ |
| **F2.3** | Validate the LLM's JSON response against the schema before storing. Retry or reject on parse failure. | Must | ✅ |
| **F2.4** | Support a `--dry-run` flag that prints the LLM's tags to stdout without writing to the DB. | Could | ✅ |
| **F2.5** | Support a `--model` flag to override the default LLM model per invocation. | Could | ⚠️ Not tested |
| **F2.6** | Truncate paper text sent to the LLM at the model's context window (with a warning). | Should | ✅ |

### 1.3 Search (`search` command)

Manual tag-based search. The user filters papers by specifying one or more tags directly - no LLM involved in the query path (NL-to-filter translation deferred to a later revision).

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **F3.1** | Accept one or more `--tag <name>` flags to filter by keyword/methodology tags (AND semantics). | Must | ✅ |
| **F3.2** | Accept `--author <name>` to filter by author (substring match). | Must | ✅ |
| **F3.3** | Accept `--field <name>` to filter by `primary_field` or `sub_field`. | Should | ✅ |
| **F3.4** | Accept `--year <YYYY>` or `--year <YYYY-YYYY>` range to filter by publication year. | Should | ✅ |
| **F3.5** | Query the local DB with the combined filters and return matching papers. | Must | ✅ |
| **F3.6** | Results printed to stdout as a table: title, authors, year, top tags. | Must | ✅ |
| **F3.7** | Support a `--json` flag to output results as JSON (for piping). | Could | ⚠️ Not tested |
| **F3.8** | Support a `--limit N` flag to cap results. | Should | ✅ |
| **F3.9** | If no papers match, print a helpful message (not an empty table). | Must | ✅ |

### 1.4 Library Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **F4.1** | `list` - print all papers in the DB, newest first. | Should | ✅ |
| **F4.2** | `list --tag <tag>` - filter by a specific tag. | Could | ✅ |
| **F4.3** | `remove <id>` or `remove <url>` - delete a paper and its tags from the DB. | Should | ✅ |
| **F4.4** | `show <id>` - print full details for one paper (all tags, abstract, URL). | Should | ✅ |
| **F4.5** | `tags` - list all distinct tags in the DB with paper counts. | Could | ✅ |

### 1.5 Configuration

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **F5.1** | Read an API key from environment variable (`PAPER_AGGREGATOR_API_KEY`), the user brings their own key. | Must | ✅ |
| **F5.2** | Config file at `~/.config/paper-aggregator/config.toml` (or XDG-compliant path). | Should | ✅ |
| **F5.3** | Configurable fields: `api_base_url` (OpenAI-compatible endpoint), `model` name, `max_context_tokens`, `db_path`, `pdf_storage_path`. | Must | ✅ |
| **F5.4** | `init` command to scaffold a default config file interactively. | Could | ✅ |

---

## 2. Non-Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| **NF1** | **Offline-first**: the DB is always local; the tool works without internet for `search`/`list`/`show`/`tags`/`remove`. | ✅ |
| **NF2** | **OpenAI-compatible API**: the LLM backend speaks the OpenAI chat completions format. The user configures `api_base_url` and brings their own key - works with OpenAI, local Ollama, LiteLLM proxy, or any compatible endpoint. | ✅ |
| **NF3** | **Graceful failures**: broken URLs, unparseable PDFs, LLM timeouts, and invalid LLM JSON must produce clear errors without crashing or corrupting the DB. | ✅ |
| **NF4** | **Idempotent ingestion**: adding the same URL twice should be safe (skip or update, never duplicate). | ✅ |
| **NF5** | **Token efficiency**: only send the first ~6000 characters (or a configurable slice) of a paper's text to the LLM - enough for the title, abstract, intro, and keywords. | ✅ |
| **NF6** | **Performance**: text extraction should complete in under 30 seconds for a 50-page PDF on consumer hardware. | ❌ Not verified |
| **NF7** | **Python ≥3.12**: match the existing `pyproject.toml` constraint. | ✅ |

---

## 3. Tagging Schema

The LLM must return the following JSON structure for every paper:

```json
{
  "title": "Attention Is All You Need",
  "authors": ["Vaswani, Ashish", "Shazeer, Noam", "..."],
  "year": 2017,
  "primary_field": "Computer Science",
  "sub_field": "Natural Language Processing",
  "keywords": ["transformers", "attention mechanism", "self-attention", "sequence-to-sequence"],
  "methodology": ["deep learning", "neural networks"],
  "abstract_summary": "One-paragraph summary of the paper's contribution in plain English."
}
```

### Field semantics

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Full paper title, cleaned up. |
| `authors` | string[] | List of "LastName, FirstName" (or as parsed). |
| `year` | int \| null | Publication year. `null` if not found. |
| `primary_field` | string | Broad academic discipline (e.g. "Computer Science", "Physics", "Biology"). |
| `sub_field` | string \| null | Narrower area (e.g. "Computer Vision", "Quantum Mechanics"). |
| `keywords` | string[] | 4–8 specific topic keywords. |
| `methodology` | string[] | Techniques/algorithms used (e.g. "transformers", "randomized controlled trial"). |
| `abstract_summary` | string | Plain-English 2–4 sentence summary for quick browsing. |

---

## 4. Database Schema (Conceptual)

```
papers
├ id (integer PK)
├ url (text UNIQUE)
├ title (text)
├ year (integer, nullable)
├ primary_field (text)
├ sub_field (text, nullable)
├ abstract_summary (text)
├ content_hash (text)         -- SHA-256 of the downloaded PDF
├ file_path (text NOT NULL)   -- path to the stored PDF in the local pdfs/ folder
└ ingested_at (timestamp)

authors
├ id (integer PK)
└ name (text UNIQUE)

paper_authors (join table)
├ paper_id (FK -> papers.id)
└ author_id (FK -> authors.id)

tags (controlled vocabulary for keywords, methodology)
├ id (integer PK)
├ name (text UNIQUE)
└ category (text)             -- "keyword" or "methodology"

paper_tags (join table)
├ paper_id (FK -> papers.id)
└ tag_id (FK -> tags.id)
```

---

## 5. CLI Interface Sketch

```
paper-aggregator add <url> [<url> ...] [--force] [--dry-run] [--model <name>]
paper-aggregator search [--tag <tag>] [--author <name>] [--field <name>] [--year <YYYY|YYYY-YYYY>] [--limit N] [--json]
paper-aggregator list [--tag <tag>] [--limit N]
paper-aggregator show <id|url>
paper-aggregator remove <id|url>
paper-aggregator tags
paper-aggregator init
paper-aggregator config [--key <k>] [--value <v>]   # read/set config
```

---

## 6. Dependencies (Predicted)

| Package | Purpose |
|---------|---------|
| `httpx` | Download files from URLs (async support, modern API) |
| `pymupdf` (fitz) | PDF text extraction |
| `openai` | LLM API client (OpenAI-compatible endpoints) |
| `pydantic` | Schema validation for LLM JSON responses |
| `rich` | Pretty-printed CLI tables |
| `typer` | CLI argument parsing (built on Click, type-hint-native) |
| `tomli` / `tomli-w` | Config file read/write |

---

## 7. Resolved Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **LLM provider**: OpenAI-compatible API, user brings their own key + endpoint | Works with OpenAI, Ollama, LiteLLM, and any self-hosted model - zero vendor lock-in. |
| 2 | **PDF extraction**: PyMuPDF (fitz) | Fastest option; AGPL is acceptable for a personal/university tool. |
| 3 | **HTML parsing**: out of scope for v1 | PDF is the universal academic format; arXiv pages redirect to PDFs anyway. |
| 4 | **PDF storage**: keep PDFs in a local `pdfs/` folder, SQLite stores paths | Enables re-extraction and manual reading later without re-downloading. |
| 5 | **Full-text search**: out of scope for v1 | Tags alone are sufficient for initial recall; full-text can be layered on later. |
| 6 | **Multi-user**: single-user only | Keeps the schema and config simple. |
| 7 | **Search strategy**: manual tag/field/author/year filters, no LLM in the search path | Simpler to implement, works fully offline, and avoids LLM query ambiguity for v1. NL-to-filter translation is a natural v2 feature. |

---

## 8. Architecture & Code Quality

Per course requirements, the project must demonstrate proper software engineering practices.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **A1** | **Separation of layers**: business logic must be separated from the UI layer. The CLI is the UI; all domain logic (ingestion, tagging, search, DB access) must live in separate, independent modules callable without any CLI dependency. | Must | ✅ |
| **A2** | **SOLID principles**: single-responsibility classes/modules, dependency injection for the LLM client and DB session, interfaces that allow swapping implementations (e.g., a stub tagger for tests). | Should | ✅ |
| **A3** | **DRY & POLA**: avoid duplication across commands; each function/module should expose the least surface needed. | Should | ✅ |
| **A4** | **Design patterns**: use established patterns where they fit - Repository for DB access, Strategy for configurable LLM backends, Command for CLI actions. | Should | ✅ |
| **A5** | **Testable by design**: business logic must be callable and testable without invoking the CLI runner or touching the real network/LLM. | Must | ✅ |

---

## 9. Testing

Tests should cover the application's core logic, data processing, validation, and edge cases. The UI layer (CLI argument parsing, table rendering) does not require full coverage, but the code must be structured so that the logic layer can be exercised independently.

### 9.1 Unit Tests

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **T1.1** | **URL validation**: well-formed URLs accepted, malformed URLs rejected, unsupported schemes rejected. | Must | ✅ |
| **T1.2** | **PDF text extraction**: valid PDF -> text output, encrypted PDF -> clear error, empty PDF -> handled gracefully. | Must | ✅ |
| **T1.3** | **LLM response parsing**: valid JSON matching the schema -> parsed successfully; malformed JSON -> `ValidationError`; missing required fields -> `ValidationError`; extra fields ignored (or rejected depending on strictness config). | Must | ✅ |
| **T1.4** | **LLM response validation**: returned `year` as string -> coerced or rejected; `authors` as string instead of list -> rejected; `methodology` with non-string items -> rejected. Type and shape checks for every schema field. | Must | ✅ |
| **T1.5** | **Deduplication logic**: adding the same URL twice -> second call returns "already ingested" without modifying the DB; adding a different URL whose content hash matches an existing paper -> skip; `--force` re-ingests and overwrites. | Must | ⚠️ URL dedup only |
| **T1.6** | **File-type detection**: `.pdf` extension -> handled as PDF; `.txt` -> handled as plain text; `.docx` / `.png` / other unsupported -> rejected with clear message. Content-Type header takes precedence over extension. | Must | ✅ |
| **T1.7** | **Search query building**: `--tag` filters combine with AND; `--author` performs case-insensitive substring match; `--year` exact and range work correctly; no filters -> returns all papers; no matches -> empty table with info message. | Must | ✅ |
| **T1.8** | **Config loading**: environment variable `PAPER_AGGREGATOR_API_KEY` read correctly; config file merged with env (env takes precedence); missing config file -> sensible defaults; invalid TOML -> clear error. | Must | ✅ |
| **T1.9** | **CRUD operations**: `list` returns newest-first; `show <id>` returns full details; `remove <id>` deletes paper + join-table rows; `tags` returns distinct tags with counts. | Must | ✅ |
| **T1.10** | **Text truncation**: paper text longer than `max_context_tokens` -> truncated correctly with a warning emitted; text shorter -> sent as-is. | Should | ✅ |

### 9.2 Integration / Edge-Case Tests

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **T2.1** | **End-to-end ingestion**: mock HTTP download -> real PDF on disk -> extract text -> mock LLM -> DB write -> verify row in DB. | Should | ✅ |
| **T2.2** | **LLM timeout / network error**: simulated timeout -> graceful error, no DB corruption, informative message to user. | Should | ❌ |
| **T2.3** | **Concurrent DB access**: two simultaneous `add` calls for different URLs -> both complete without `database locked` errors (WAL mode). | Could | ❌ |
| **T2.4** | **Empty / near-empty PDF**: PDF with no extractable text -> clear error, no DB insert. | Should | ⚠️ Extraction only |
| **T2.5** | **Unicode / non-English text**: papers with non-ASCII characters -> preserved correctly through extract -> tag -> store -> display pipeline. | Should | ❌ |

### 9.3 Test Infrastructure

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **TI.1** | Use **pytest** as the test runner. | Must | ✅ |
| **TI.2** | Tests must be runnable with a single `pytest` (or `poetry run pytest`) command from the project root. | Must | ✅ |
| **TI.3** | Use **monkeypatch** (pytest built-in) or **unittest.mock** for mocking the LLM client, HTTP downloads, and filesystem operations. No real network calls in unit tests. | Must | ✅ |
| **TI.4** | Test DB must use an in-memory SQLite database so tests are isolated and repeatable. | Must | ✅ |
| **TI.5** | Tests must be located in a `tests/` directory at the project root, mirroring the source package structure. | Must | ✅ |
| **TI.6** | Aim for ≥70% code coverage on the logic/business layer (not the CLI/UI layer). | Should | ✅ |

TI.6 verifiable with `poetry run pytest --cov=src/paper_aggregator --cov-report=term-missing`

---

## 10. Deployment & Packaging

The project must provide tooling that lets a third party install and run the application with minimal setup.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **D1** | **`pyproject.toml` as build artifact**: the project must be installable via `pip install .` (or `poetry install`) with all dependencies declared. | Must | ✅ |
| **D2** | **Docker image**: provide a `Dockerfile` that builds a runnable container with the app and all dependencies. The entrypoint should be the CLI (`paper-aggregator`). Document how to mount the config directory and `pdfs/` folder as volumes. | Should | ✅ |
| **D3** | **PyInstaller / standalone bundle**: produce a single-file executable via PyInstaller (or similar) so the tool can be used without a Python installation. | Could | ❌ |
| **D4** | **Custom setup script**: a `setup.sh` or `install.sh` that creates a virtual environment, installs dependencies, and optionally symlinks the entry point into `~/.local/bin`. | Could | ❌ |
| **D5** | At least **one** deployment method (beyond bare `poetry install`) must be documented and working. | Must | ✅ Docker |
| **D6** | The deployment artifact must handle the `PAPER_AGGREGATOR_API_KEY` env var being set at runtime (not baked into the image/bundle). | Must | ✅ |

---

## 11. Documentation

Documentation is part of the project grading (10%). The codebase must be self-documenting for developers and accompanied by user-facing instructions.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **DOC1** | **`README.md`** at the repo root covering: project description, features, dependencies, how to install, how to run, how to test, configuration reference (env vars + config file), and a link to this REQUIREMENTS.md. | Must | ✅ |
| **DOC2** | **User documentation**: a `docs/` directory or a section in README with walkthrough examples for `add`, `search`, `list`, `show`, `remove`, `tags`, `init`, and `config`. | Should | ✅ |
| **DOC3** | **Technical documentation**: module-level docstrings describing purpose and public API; class/method docstrings for non-obvious logic. | Should | ✅ |
| **DOC4** | **Architecture overview**: a brief section in README (or a linked `ARCHITECTURE.md`) describing the layered structure - CLI layer -> command handlers -> domain services -> repositories -> DB / LLM client. | Should | ✅ |
| **DOC5** | **Inline code comments**: document *why*, not *what* - explain design choices, workarounds, and non-obvious behavior. | Should | ✅ |

---

## 12. Version Control

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **VCS1** | The project must use **git** for version control throughout development. | Must | ✅ |
| **VCS2** | Commits should be granular, well-described (conventional commit style preferred: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`). | Should | ⚠️ Inconsistent |
| **VCS3** | The repository must contain the full history - not a single squashed commit at submission. | Must | ✅ |

---

## 13. Minimum Project Scope (Course Checklist)

Recap of the course-mandated minimum scope, cross-referenced with this document:

| Scope item | Covered by |
|------------|------------|
| User interface | CLI (§5) - GUI deferred per project plan |
| Business logic layer | §1 (all functional requirements) + §8 (architecture) |
| Persistent data storage or external API | SQLite DB (§4) + OpenAI-compatible LLM API (§1.2) |
| Error handling & input validation | §2 NF3 + F1.7 + F2.3 + T1.1–T1.4 |
| Unit tests for key functions | §9 |
| Documentation & deployment instructions | §10 + §11 |
