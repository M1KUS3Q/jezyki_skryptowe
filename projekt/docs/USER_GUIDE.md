# Paper Aggregator - User Guide

A walkthrough of every command with real examples.

## Prerequisites

1. **Python ≥ 3.12** installed.
2. **An API key** for an OpenAI-compatible endpoint (OpenAI, Ollama, LiteLLM, etc.).
3. The tool installed via `pip install .` or `poetry install`.

Set your API key:

```bash
export PAPER_AGGREGATOR_API_KEY="sk-..."
```

Or place it in a `.env` file in the project directory.

---

## `init` - Scaffold a config file

Creates `~/.config/paper-aggregator/config.toml` interactively:

```bash
$ paper-aggregator init

API base URL [https://api.openai.com/v1]:
Default model [gpt-4o-mini]:
Max context characters [6000]:
✓ Config written to /home/user/.config/paper-aggregator/config.toml
```

Press Enter at each prompt to accept the default, or type a custom value.

If a config already exists, you'll be asked whether to overwrite.

---

## `config` - Read or change settings

**View the whole config file:**

```bash
$ paper-aggregator config
```

Prints the contents of `config.toml`.

**View a single key:**

```bash
$ paper-aggregator config --key model
model = gpt-4o-mini
```

**Change a setting:**

```bash
$ paper-aggregator config --key model --value "gpt-4o"
✓ Set model = gpt-4o
```

Allowed keys: `api_base_url`, `model`, `max_context_chars`, `db_path`, `pdf_storage_path`.

---

## `add` - Ingest papers

The core command. Downloads a paper, extracts its text, sends it to the LLM for tagging, and stores everything in the local database.

### Basic usage

```bash
paper-aggregator add https://arxiv.org/pdf/1706.03762.pdf
```

Output:

```
Processing: https://arxiv.org/pdf/1706.03762.pdf
  ✓ Downloaded (a1b2c3d4…)
  ✓ Extracted 52341 characters.
  ✓ Tagged - title: 'Attention Is All You Need'
  ✓ Stored in database (ID: 1).
  ✓ PDF stored at /home/user/.local/share/paper-aggregator/pdfs/1.pdf
```

### Multiple URLs at once

```bash
paper-aggregator add https://arxiv.org/pdf/1706.03762.pdf https://arxiv.org/pdf/1810.04805.pdf
```

### Preview tags without saving (`--dry-run`)

```bash
paper-aggregator add --dry-run https://arxiv.org/pdf/1706.03762.pdf
```

Prints the LLM's JSON response to stdout but does **not** write to the database.

### Override the LLM model

```bash
paper-aggregator add --model gpt-4o https://arxiv.org/pdf/1706.03762.pdf
```

### Re-ingest a paper (`--force`)

If a URL was already ingested, `add` skips it. Use `--force` to overwrite:

```bash
paper-aggregator add --force https://arxiv.org/pdf/1706.03762.pdf
```

### Add a local PDF file

```bash
paper-aggregator add /tmp/my-paper.pdf
```

> **macOS note:** Python cannot read files in `~/Downloads`, `~/Desktop`, or `~/Documents` due to sandboxing. Move the file to `/tmp/` or another unrestricted location first.

---

## `search` - Find papers in your library

Works fully offline - no LLM involved in the search path.

### By tag

```bash
paper-aggregator search --tag transformers
```

Multiple tags use AND semantics (paper must have **all** specified tags):

```bash
paper-aggregator search --tag transformers --tag "attention mechanism"
```

### By author (fuzzy match)

```bash
paper-aggregator search --author Vaswani
```

Finds "Vaswani, Ashish" even if you only type part of the name. Disable fuzzy matching with `--no-fuzzy`.

### By field

```bash
paper-aggregator search --field "Natural Language Processing"
```

Matches against both `primary_field` and `sub_field`.

### By year

Exact year:

```bash
paper-aggregator search --year 2017
```

Year range:

```bash
paper-aggregator search --year 2017-2023
```

### Combine filters

```bash
paper-aggregator search --tag nlp --author Vaswani --year 2017-2020 --limit 10
```

### JSON output

```bash
paper-aggregator search --tag transformers --json
```

Useful for piping to `jq` or other tools.

### BibTeX output

```bash
paper-aggregator search --tag nlp --bibtex
```

---

## `list` - Browse all papers

```bash
paper-aggregator list
```

Newest papers first. Optionally filter by a single tag:

```bash
paper-aggregator list --tag nlp
```

Limit results:

```bash
paper-aggregator list --limit 5
```

BibTeX output:

```bash
paper-aggregator list --bibtex
```

---

## `show` - Full details for one paper

By ID:

```bash
$ paper-aggregator show 1

Title: Attention Is All You Need
ID: 1
URL: https://arxiv.org/pdf/1706.03762.pdf
Authors: Vaswani, Ashish; Shazeer, Noam; ...
Year: 2017
Field: Computer Science / Natural Language Processing
Keywords: transformers, attention mechanism, self-attention, ...
Methodology: deep learning, neural networks
Abstract: The dominant sequence transduction models are based on...
File: /home/user/.local/share/paper-aggregator/pdfs/1.pdf
Ingested at: 2025-06-25 12:34:56
```

By URL:

```bash
paper-aggregator show https://arxiv.org/pdf/1706.03762.pdf
```

---

## `bibtex` - Generate a citation

```bash
$ paper-aggregator bibtex 1

@article{vaswani2017attention,
  author = {Vaswani, Ashish and Shazeer, Noam and ...},
  title = {Attention Is All You Need},
  year = {2017},
  note = {The dominant sequence transduction models are based on...}
}
```

Choose the entry type:

```bash
paper-aggregator bibtex 1 --type inproceedings
```

Save to a file:

```bash
paper-aggregator bibtex 1 --output refs.bib
```

---

## `remove` - Delete a paper

By ID:

```bash
paper-aggregator remove 1
```

By URL:

```bash
paper-aggregator remove https://arxiv.org/pdf/1706.03762.pdf
```

This deletes the paper, its authors, and its tags from the database. The PDF file in the `pdfs/` folder is **not** deleted - you can remove it manually if needed.

---

## `tags` - List all tags

```bash
$ paper-aggregator tags

┌──────────────────────┬─────────────┬────────┐
│ Tag                  │ Category    │ Papers │
├──────────────────────┼─────────────┼────────┤
│ transformers         │ keyword     │      3 │
│ attention mechanism  │ keyword     │      2 │
│ deep learning        │ methodology │      5 │
│ neural networks      │ methodology │      4 │
└──────────────────────┴─────────────┴────────┘
```

---

## Docker usage

If you prefer running via Docker, add this alias to `~/.zshrc` or `~/.bashrc`:

```bash
alias paper='docker run --rm \
  -e PAPER_AGGREGATOR_API_KEY \
  -v "${XDG_CONFIG_HOME:-$HOME/.config}/paper-aggregator:/config" \
  -v "${XDG_DATA_HOME:-$HOME/.local/share}/paper-aggregator:/data" \
  paper-aggregator'
```

Then use `paper` exactly like `paper-aggregator`:

```bash
paper init
paper add https://arxiv.org/pdf/1706.03762.pdf
paper search --tag transformers
```

---

## Configuration reference

### Environment variables

| Variable | Purpose |
|----------|---------|
| `PAPER_AGGREGATOR_API_KEY` | API key for your LLM provider (**required for `add`**) |
| `XDG_CONFIG_HOME` | Override config directory (default: `~/.config`) |
| `XDG_DATA_HOME` | Override data directory (default: `~/.local/share`) |

### Config file (`~/.config/paper-aggregator/config.toml`)

```toml
api_base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
max_context_chars = 6000
# db_path = "/custom/path/papers.db"
# pdf_storage_path = "/custom/path/pdfs"
```

Environment variables take precedence over the config file.

### Data directory layout

```
~/.local/share/paper-aggregator/
├── papers.db          # SQLite database
└── pdfs/              # Downloaded PDFs (one per paper, named by ID)
    ├── 1.pdf
    ├── 2.pdf
    └── ...
```
