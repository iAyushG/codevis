# codevis

A codebase intelligence tool that turns any git repository into an
interactive dependency graph — colored by risk.

Point it at any Python project and get:
- **Dependency map** — which files import which
- **Churn heatmap** — which files change most often (git history)
- **Co-change coupling** — files that always change together
- **Risk scores** — normalized 0 to 1 score per file based on commit frequency
- **Impact analysis** — click any file to see what breaks if you change it

Built as an MCP server so Claude can analyze your codebase directly
in conversation. Also ships a web UI and a CLI.

---

## Demo

*Analyzing the `requests` library — 462 files tracked, 89 dependency
edges, hottest file: `requests/models.py` with 717 changes*

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
path and click Analyze. The graph renders automatically with nodes
colored by risk score. Click any node to see its impact — what breaks
if you change it.

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

## Available MCP tools

| Tool | What it does |
|---|---|
| `list_files` | Lists all code files in a repo |
| `get_dependencies` | Returns dependency graph as nodes and edges |
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

**Impact analysis** uses NetworkX graph traversal — ancestors are
files that import this file (will break), descendants are files this
file imports (dependencies).

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
    ├── parser.py       # AST dependency parser
    ├── git_miner.py    # Git churn and co-change analysis
    ├── graph.py        # NetworkX graph builder (coming soon)
    └── metrics.py      # Complexity metrics (coming soon)
```

---

## Roadmap

- [x] JavaScript and TypeScript support
- [ ] Shareable graph URLs
- [ ] GitHub Action for CI integration
- [ ] Diff view between two commits
- [ ] AI-powered architecture explainer
- [ ] Multi-language support via tree-sitter

---

## Author

Built by **Ayush Gupta** — [github.com/iAyushG](https://github.com/iAyushG)

If you find a bug or want to contribute, open an issue. This is an
early-stage tool and feedback from real users shapes what gets built
next.

---

## License

MIT — see [LICENSE](LICENSE) for details.