# COMP3011 Coursework 2 — Search Engine Tool

Individual coursework for **Web Services and Web Data (COMP3011)**. This repository implements a small **command-line search tool** that crawls [quotes.toscrape.com](https://quotes.toscrape.com/), builds an **inverted index** with per-page statistics, persists it to disk, and supports interactive **print** and **find** queries.

## Project overview

The tool is split into four modules under `src/`:

| Module | Role |
|--------|------|
| `crawler.py` | Fetches pages with a **6s** delay, **Breadth First Search** same domain crawl, `robots.txt` checks |
| `indexer.py` | Parses HTML text, tokenizes, **lowercases**, drops **stopwords**, **stems** (Porter), records **frequency** and **token positions** per URL |
| `search.py` | **AND** multi word queries over the index, **ranked** by summed term frequencies; `print`-style lookup uses the same normalization |
| `main.py` | Interactive shell: `build`, `load`, `print`, `find`, `quit` |

The compiled index is written to **`data/index.json`** (create this by running `build`, or submit the file as required by the brief).

## Requirements

- **Python 3.10+** (3.11 or 3.12 recommended)
- Packages listed in `requirements.txt` (install via `pip` below)

## Installation and setup

From the **repository root** (the folder that contains `src/`, `tests/`, and `requirements.txt`):

```bash
python -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **macOS / Linux:** `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

**Note:** The indexer uses NLTK’s `PorterStemmer` only; no extra NLTK corpora download is required for the current code paths.

## Usage

Always run the CLI **from the repository root** so the index path `data/index.json` is resolved correctly and imports resolve as intended:

```bash
python src/main.py
```

You will see a prompt `> `. Type commands as below. Exit with `quit` or `exit`.

### Command: `build`

Crawls the target site, builds the inverted index, creates `data/` if needed, and saves **`data/index.json`**.

```text
> build
```

**Warning:** The crawler enforces a **6-second delay between HTTP requests**.

### Command: `load`

Loads a previously saved index from **`data/index.json`** (no network crawl).

```text
> load
```

Run this after a fresh shell session if you already built the index and do not want to crawl again.

### Command: `print <word>`

Prints the **inverted index postings** for one query word: for each URL, **frequency** and **positions** (token indices in the page’s token stream after normalization). Lookup is **case-insensitive** and uses the same **stemming** as indexing.

```text
> print whatever-word-you-want
```

### Command: `find <query>`

Finds pages that contain **all** whitespace separated terms (**AND** semantics). Results are **ranked** by the **sum of term frequencies** across the query terms on each page. Normalization matches the indexer (lowercase + stemming).

Single word:

```text
> find indifference
```

Multi word (brief example style):

```text
> find good friends
```

## Testing

From the **repository root**, with the virtual environment activated and dependencies installed:

```bash
python -m pytest tests -q
```

Optional coverage report (uses `pytest-cov` from `requirements.txt`):

```bash
python -m pytest tests --cov=src --cov-report=term-missing
```

Tests use mocking for HTTP where appropriate so the suite does not hit the live site.

## Dependencies

Declared in **`requirements.txt`**:

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client for crawling and `robots.txt` |
| `beautifulsoup4` | HTML parsing and visible text extraction |
| `nltk` | Porter stemmer for indexing and search |
| `pytest` | Test runner |
| `pytest-cov` | Optional coverage reporting |

Install with `pip install -r requirements.txt` as above.

## Repository layout (coursework structure)

```text
repository-root/
├── src/
│   ├── crawler.py
│   ├── indexer.py
│   ├── search.py
│   └── main.py
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
├── data/
│   └── index.json          # produced by `build`; submit per brief
├── requirements.txt
└── README.md
```

## Academic integrity and GenAI

This module’s brief requires a **clear declaration** of any **generative AI** tools used and a **critical evaluation** in the **video demonstration**. Ensure your submitted video and any written declarations match your actual use of tools, per University and module rules.

## Licence / course use

This project is submitted as **assessed coursework**. The target website **quotes.toscrape.com** is intended for scraping practice; this tool still uses a politeness delay and respects `robots.txt` in code as implemented in `crawler.py`.
