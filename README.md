# codevis

A codebase intelligence tool that turns any git repository into an
interactive dependency graph — colored by risk.

Point it at any Python project and get:
- **Dependency map** — which files import which
- **Churn heatmap** — which files change most often (git history)
- **Co-change coupling** — files that always change together
- **Risk scores** — normalized 0→1 score per file based on commit frequency

Built as an MCP server so Claude can analyze your codebase directly
in conversation. Also ships a CLI that produces a JSON file you can
visualize with any graph tool or feed directly to Claude.

---

## Demo

*Analyzing the `requests` library — 462 files tracked, 89 dependency
edges, hottest file: `models.py` with 717 changes*

---

## Installation

**Requirements:** Python 3.11+, Git, [uv](https://astral.sh/uv)

```bash
git clone https://github.com/iayus/codevis.git
cd codevis
uv sync
```

---

## Usage

### Option 1 — CLI (recommended for large repos)

Run the full analysis and save to JSON:

```bash
uv run python analyze.py /path/to/your/repo
```

This produces `analysis.json` with nodes, edges, churn scores, and
co-change pairs. Upload that file to Claude and ask it to visualize
the dependency graph colored by risk score.

### Option 2 — MCP server (Claude Desktop)

Add to your Claude Desktop config file.

**Windows** — open Claude Desktop → Settings → Developer → Edit Config:

```json
{
  "mcpServers": {
    "codevis": {
      "command": "C:\\path\\to\\codevis\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\codevis\\server.py"]
    }
  }
}
```

Replace `C:\\path\\to\\codevis` with your actual install path, then
restart Claude Desktop.

Then ask Claude:
analyze the dependencies in /path/to/your/repo
show me the hotspots in /path/to/your/repo
list all files in /path/to/your/repo

---

## Available MCP tools

| Tool | What it does |
|---|---|
| `list_files` | Lists all code files in a repo |
| `get_dependencies` | Returns dependency graph as nodes + edges |
| `get_hotspots` | Returns churn scores and co-change pairs from git history |

---

## How it works

**Dependency analysis** uses Python's built-in `ast` module to parse
import statements without executing any code. Fast and safe.

**Git analysis** runs `git log` and counts how many times each file
appears across all commits. Co-change coupling finds file pairs that
appear in the same commit more than once.

**Risk score** is `file_changes / max_changes_in_repo` — normalized
so the hottest file always scores 1.0 and everything else is relative
to it.

---

## Roadmap

- [ ] JavaScript / TypeScript support
- [ ] Impact analysis — "if I change X, what breaks?"
- [ ] Web frontend with interactive force-directed graph
- [ ] Background job system for large repos
- [ ] GitHub Action for CI integration
- [ ] AI-powered architecture explainer

---

## Author

Built by **Ayush Gupta**.

If you use this project, find a bug, or want to contribute — open an
issue or reach out. This is an early-stage tool and feedback from real
users shapes what gets built next.

---

## License

MIT License — Copyright (c) 2026 Ayush Gupta

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software to use, copy, modify, merge, publish, and
distribute it, subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.