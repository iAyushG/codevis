import ast
import os
from pathlib import Path


def get_imports(filepath: str) -> list[str]:
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

    for imp in imports:
        imp_path = imp.replace('.', os.sep) + '.py'
        for f in all_files:
            if f.endswith(imp_path):
                local_deps.append(f)
                break

    return local_deps


def analyze_repo(repo_path: str) -> dict:
    """Scan an entire repo and return nodes and edges for the graph"""
    all_py_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs
                   if d not in ['.git', 'node_modules', '__pycache__', '.venv']]
        for f in files:
            if f.endswith('.py'):
                all_py_files.append(os.path.join(root, f))

    nodes = []
    edges = []

    for filepath in all_py_files:
        size = os.path.getsize(filepath)
        nodes.append({
            "id": filepath,
            "label": os.path.relpath(filepath, repo_path),
            "size": size,
            "language": "python"
        })

        imports = get_imports(filepath)
        local_deps = resolve_local_imports(filepath, imports, all_py_files)

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
            "repo_path": repo_path
        }
    }