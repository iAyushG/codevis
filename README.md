# codevis

A codebase intelligence tool that turns any git repository into an
interactive dependency graph — colored by risk.

Point it at any Python or JavaScript project and get:
- **Dependency map** — which files import which
- **Churn heatmap** — which files change most often (git history)
- **Co-change coupling** — files that always change together
- **Risk scores** — normalized 0 to 1 score per file based on commit frequency
- **Impact analysis** — click any file to see what breaks if you change it
- **Language detection** — Python, JavaScript, TypeScript color coded

Built as an MCP server so Claude can analyze your codebase directly
in conversation. Also ships a web UI and a CLI.

---

## Demo

*Analyzing the `requests` library — 462 files tracked, 89 dependency
edges, hottest file: `requests/models.py` with 717 changes*

*Analyzing `express` — 141 files, 158 dependencies, all JavaScript*

---

## Installation

**Requirements:** Python 3.11+, Git, [uv](https://astral.sh/uv)

```bash
git clone https://github.com/iAyushG/codevis.git
cd codevis
uv sync
```

---

## Usage

### Option 1 — Web UI (recommended)

Start the web server:

```bash
uv run python web.py
```

Open `http://localhost:8000` in your browser. Enter any local repo
path and click Analyze.

Features:
- Force-directed dependency graph with zoom and pan
- Nodes colored by risk score (red = high churn, green = low)
- Language color coded inner dot (green = Python, yellow = JS, blue = TS)
- Node size proportional to git churn
- Hover any node to highlight its direct connections
- Click any node for impact analysis — what breaks if you change it
- Search bar to find and jump to any file instantly
- Top hotspots list in the sidebar

### Option 2 — CLI (good for large repos or scripting)

Run the full analysis and save to JSON:

```bash
uv run python analyze.py /path/to/your/repo
```

This produces `analysis.json` with all nodes, edges, churn scores,
and co-change pairs. Upload that file to Claude and ask it to
visualize the dependency graph colored by risk score.

### Option 3 — MCP server (Claude Desktop)

Add to your Claude Desktop config file.

**Windows** — open Claude Desktop, go to Settings, Developer,
then click Edit Config:

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

## Supported languages

| Language | Dependency parsing | Git analysis |
|---|---|---|
| Python | yes (ast module) | yes |
| JavaScript | yes (regex, ES modules + CommonJS) | yes |
| TypeScript | yes (regex, ES modules) | yes |
| C++ / Java | coming soon | yes |

---

## Available MCP tools

| Tool | What it does |
|---|---|
| `list_files` | Lists all code files in a repo |
| `get_dependencies` | Returns dependency graph as nodes and edges |
| `get_hotspots` | Returns churn scores and co-change pairs from git history |

---

## How it works

**Dependency analysis** uses Python's built-in `ast` module for Python
files and regex for JavaScript and TypeScript. No code is executed.

**Git analysis** runs `git log` and counts how many times each file
appears across all commits. Co-change coupling finds file pairs that
appear in the same commit more than once.

**Risk score** is `file_changes / max_changes_in_repo` — normalized
so the hottest file always scores 1.0 and everything else is relative.

**Impact analysis** uses NetworkX graph traversal. Ancestors are files
that import this file (will break if you change it), descendants are
files this file imports.

**Web server** runs analysis in a background thread so there are no
timeouts. The browser polls every 800ms until the job completes.

---

## Project structure

```
codevis/
├── web.py              # FastAPI web server + background jobs
├── server.py           # MCP server for Claude Desktop
├── analyze.py          # CLI script, outputs analysis.json
├── static/
│   └── index.html      # D3 force-directed graph frontend
└── codevis/
├── parser.py       # AST + regex dependency parser (Python, JS, TS)
├── git_miner.py    # Git churn and co-change analysis
├── graph.py        # NetworkX graph builder (coming soon)
└── metrics.py      # Complexity metrics (coming soon)
```

---

## Roadmap

- [x] Python dependency parsing
- [x] JavaScript and TypeScript support
- [x] Git churn heatmap
- [x] Impact analysis
- [x] Interactive web UI with D3
- [x] MCP server for Claude Desktop
- [ ] Circular dependency detection
- [ ] Shareable graph URLs
- [ ] GitHub Action for CI integration
- [ ] Dead code detection
- [ ] C++ and Java support

---

## Author

Built by **Ayush Gupta** — [github.com/iAyushG](https://github.com/iAyushG)

If you find a bug or want to contribute, open an issue. This is an
early-stage tool and feedback from real users shapes what gets built
next.

---

## License

MIT — see [LICENSE](LICENSE) for details.