from mcp.server.fastmcp import FastMCP
import os
from codevis.parser import analyze_repo
from codevis.git_miner import get_git_stats

mcp = FastMCP("codevis")


@mcp.tool()
def list_files(repo_path: str) -> list[str]:
    """List all code files in a repository folder"""
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs 
                   if d not in ['.git', 'node_modules', '__pycache__', '.venv']]
        for f in filenames:
            if f.endswith(('.py', '.js', '.ts', '.cpp', '.h', '.java')):
                files.append(os.path.join(root, f))
    return files


@mcp.tool()
def get_dependencies(repo_path: str) -> dict:
    """Analyze a repository and return its dependency graph as nodes and edges"""
    return analyze_repo(repo_path)


@mcp.tool()
def get_hotspots(repo_path: str) -> dict:
    """Analyze git history to find risky high-churn files and coupled pairs"""
    return get_git_stats(repo_path)


if __name__ == "__main__":
    mcp.run()