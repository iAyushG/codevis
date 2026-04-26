import ast
import os
import re
from pathlib import Path


# ── Python parser ───────────────────────────────────────────────

def get_python_imports(filepath: str) -> list[str]:
    """Read a Python file and return all the modules it imports"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        tree = ast.parse(source)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    except Exception:
        return []


# ── JavaScript / TypeScript parser ─────────────────────────────

# Matches all common JS/TS import styles
JS_IMPORT_PATTERNS = [
    # import X from './module'
    # import { X } from './module'
    # import './module'
    r"""import\s+(?:[^'"]*\s+from\s+)?['"]([^'"]+)['"]""",
    # const X = require('./module')
    # require('./module')
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
    # import('./module')  -- dynamic imports
    r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""",
]

JS_IMPORT_RE = re.compile(
    '|'.join(f'(?:{p})' for p in JS_IMPORT_PATTERNS)
)


def get_js_imports(filepath: str) -> list[str]:
    """Read a JS/TS file and return all the modules it imports"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()

        imports = []
        for match in JS_IMPORT_RE.finditer(source):
            # Each pattern has one capture group, find the one that matched
            module = next((g for g in match.groups() if g is not None), None)
            if module:
                imports.append(module)

        return imports

    except Exception:
        return []


# ── Language router ─────────────────────────────────────────────

LANGUAGE_MAP = {
    '.py':  'python',
    '.js':  'javascript',
    '.jsx': 'javascript',
    '.ts':  'typescript',
    '.tsx': 'typescript',
    '.cpp': 'cpp',
    '.h':   'cpp',
    '.java':'java',
}

def get_imports(filepath: str) -> list[str]:
    """Route to the correct import extractor based on file extension"""
    ext = Path(filepath).suffix.lower()
    if ext == '.py':
        return get_python_imports(filepath)
    elif ext in ('.js', '.jsx', '.ts', '.tsx'):
        return get_js_imports(filepath)
    # cpp/java not yet implemented — return empty
    return []


def get_language(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    return LANGUAGE_MAP.get(ext, 'unknown')


# ── Local import resolver ───────────────────────────────────────

def resolve_local_imports(
    filepath: str,
    imports: list[str],
    all_files: list[str]
) -> list[str]:
    """Figure out which imports are local files vs external libraries.

    Note: currently uses simple suffix matching. A future improvement
    is to anchor resolution to the repo root for accuracy on
    deeply nested packages.
    """
    local_deps = []
    ext = Path(filepath).suffix.lower()

    for imp in imports:
        if ext == '.py':
            # Python: dotted module name -> path
            imp_path = imp.replace('.', os.sep) + '.py'
            for f in all_files:
                if f.endswith(imp_path):
                    local_deps.append(f)
                    break

        elif ext in ('.js', '.jsx', '.ts', '.tsx'):
            # JS/TS: only resolve relative imports (start with . or ..)
            if not imp.startswith('.'):
                continue

            # Try each possible extension
            base_dir = os.path.dirname(filepath)
            raw = os.path.normpath(os.path.join(base_dir, imp))

            candidates = [
                raw,
                raw + '.js',
                raw + '.jsx',
                raw + '.ts',
                raw + '.tsx',
                os.path.join(raw, 'index.js'),
                os.path.join(raw, 'index.ts'),
            ]

            for candidate in candidates:
                if candidate in all_files:
                    local_deps.append(candidate)
                    break

    return local_deps


def _find_repo_root(filepath: str, all_files: list[str]) -> str:
    """Find the common root folder of all files.

    Used to anchor import resolution — wired in when multi-package
    support is added.
    """
    if not all_files:
        return os.path.dirname(filepath)
    paths = [Path(f) for f in all_files]
    common = paths[0].parent
    for p in paths[1:]:
        while common not in p.parents and common != p.parent:
            common = common.parent
    return str(common)


# ── Repo analyzer ───────────────────────────────────────────────

SUPPORTED_EXTENSIONS = ('.py', '.js', '.jsx', '.ts', '.tsx')

def analyze_repo(repo_path: str) -> dict:
    """Scan an entire repo and return nodes and edges for the graph"""
    all_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs
                   if d not in [
                       '.git', 'node_modules', '__pycache__',
                       '.venv', 'dist', 'build', '.next', 'coverage'
                   ]]
        for f in files:
            if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS:
                all_files.append(os.path.join(root, f))

    nodes = []
    edges = []

    for filepath in all_files:
        size = os.path.getsize(filepath)
        nodes.append({
            "id": filepath,
            "label": os.path.relpath(filepath, repo_path),
            "size": size,
            "language": get_language(filepath)
        })

        imports = get_imports(filepath)
        local_deps = resolve_local_imports(filepath, imports, all_files)

        for dep in local_deps:
            edges.append({
                "source": filepath,
                "target": dep,
                "type": "imports"
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_files": len(nodes),
            "total_dependencies": len(edges),
            "repo_path": repo_path,
            "languages": list(set(
                get_language(f) for f in all_files
            ))
        }
    }