import json
import os
import threading
from pathlib import Path

import networkx as nx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from codevis.git_miner import get_git_stats
from codevis.parser import analyze_repo

app = FastAPI(title="codevis")

jobs = {}


def compute_cycles(dep_data: dict) -> list:
    """Find all circular dependencies, filter self-loops"""
    G = nx.DiGraph()
    for edge in dep_data["edges"]:
        G.add_edge(edge["source"], edge["target"])

    node_label = {n["id"]: n["label"] for n in dep_data["nodes"]}

    raw_cycles = list(nx.simple_cycles(G))
    cycles = []
    for cycle in raw_cycles:
        if len(cycle) > 1:
            cycles.append({
                "files": [node_label.get(n, n) for n in cycle],
                "ids": cycle,
                "length": len(cycle)
            })

    cycles.sort(key=lambda x: x["length"])
    return cycles


def run_analysis(job_id: str, repo_path: str):
    """Run in background thread — no timeout issues"""
    try:
        jobs[job_id] = {"status": "running", "step": "git analysis"}

        git_data = get_git_stats(repo_path)
        jobs[job_id]["step"] = "dependency analysis"

        dep_data = analyze_repo(repo_path)
        jobs[job_id]["step"] = "detecting cycles"

        cycles = compute_cycles(dep_data)
        jobs[job_id]["step"] = "merging results"

        for node in dep_data["nodes"]:
            label = node["label"].replace("\\", "/")
            churn_info = git_data["churn"].get(label, {})
            node["changes"] = churn_info.get("changes", 0)
            node["risk_score"] = churn_info.get("risk_score", 0)

        jobs[job_id] = {
            "status": "done",
            "result": {
                "repo": repo_path,
                "summary": {
                    "total_files": dep_data["summary"]["total_files"],
                    "total_dependencies": dep_data["summary"]["total_dependencies"],
                    "total_files_tracked_by_git": git_data["summary"]["total_files_tracked"],
                    "hottest_file": git_data["summary"]["hottest_file"],
                    "coupled_pairs": git_data["summary"]["coupled_pairs"],
                    "languages": dep_data["summary"].get("languages", []),
                    "total_cycles": len(cycles),
                },
                "nodes": dep_data["nodes"],
                "edges": dep_data["edges"],
                "churn": git_data["churn"],
                "cochange": git_data["cochange"],
                "cycles": cycles,
            }
        }

    except Exception as e:
        jobs[job_id] = {"status": "error", "message": str(e)}


@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path("static/index.html")
    if html_path.exists():
        return html_path.read_text()
    return HTMLResponse("<h2>codevis loading...</h2>")


@app.post("/analyze")
def start_analysis(repo_path: str):
    """Start analysis in background, return job id immediately"""
    job_id = str(len(jobs) + 1)
    jobs[job_id] = {"status": "pending"}
    thread = threading.Thread(
        target=run_analysis,
        args=(job_id, repo_path),
        daemon=True
    )
    thread.start()
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """Check if analysis is done"""
    if job_id not in jobs:
        return JSONResponse({"status": "not_found"}, status_code=404)
    job = jobs[job_id]
    if job["status"] == "done":
        return job
    return {"status": job["status"], "step": job.get("step", "")}


@app.get("/cycles")
def get_cycles(repo_path: str):
    """Find all circular dependencies in the repo"""
    dep_data = analyze_repo(repo_path)
    cycles = compute_cycles(dep_data)
    return {
        "total_cycles": len(cycles),
        "cycles": cycles[:20]
    }


@app.get("/impact")
def get_impact(repo_path: str, file: str):
    """What breaks if this file changes?"""
    dep_data = analyze_repo(repo_path)

    G = nx.DiGraph()
    for edge in dep_data["edges"]:
        G.add_edge(edge["source"], edge["target"])

    target_node = None
    file_normalized = file.replace('/', os.sep).replace('\\', os.sep)
    for node in dep_data["nodes"]:
        label_normalized = node["label"].replace('/', os.sep).replace('\\', os.sep)
        if label_normalized == file_normalized or node["id"].endswith(file_normalized):
            target_node = node["id"]
            break

    if not target_node:
        return {"error": f"File '{file}' not found in repo"}

    if target_node not in G:
        return {
            "file": file,
            "if_you_change_this": {"files_that_import_it": [], "count": 0},
            "this_file_depends_on": {"files_it_imports": [], "count": 0}
        }

    ancestors = list(nx.ancestors(G, target_node))
    descendants = list(nx.descendants(G, target_node))

    return {
        "file": file,
        "if_you_change_this": {
            "files_that_import_it": ancestors,
            "count": len(ancestors)
        },
        "this_file_depends_on": {
            "files_it_imports": descendants,
            "count": len(descendants)
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)