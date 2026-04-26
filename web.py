import json
import os
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from codevis.git_miner import get_git_stats
from codevis.parser import analyze_repo

app = FastAPI(title="codevis")

# Store job results in memory
jobs = {}


def run_analysis(job_id: str, repo_path: str):
    """Run in background thread — no timeout issues"""
    try:
        jobs[job_id] = {"status": "running", "step": "git analysis"}

        git_data = get_git_stats(repo_path)
        jobs[job_id]["step"] = "dependency analysis"

        dep_data = analyze_repo(repo_path)
        jobs[job_id]["step"] = "merging results"

        # Merge churn into nodes
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
                },
                "nodes": dep_data["nodes"],
                "edges": dep_data["edges"],
                "churn": git_data["churn"],
                "cochange": git_data["cochange"],
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


@app.get("/impact")
def get_impact(repo_path: str, file: str):
    """What breaks if this file changes?"""
    import networkx as nx
    dep_data = analyze_repo(repo_path)
    
    G = nx.DiGraph()
    for edge in dep_data["edges"]:
        G.add_edge(edge["source"], edge["target"])
    
    # Find the node that matches the file label
    target_node = None
    for node in dep_data["nodes"]:
        if file in node["label"] or file in node["id"]:
            target_node = node["id"]
            break
    
    if not target_node:
        return {"error": f"File '{file}' not found in repo"}
    
    # Everything that depends ON this file (upstream)
    ancestors = list(nx.ancestors(G, target_node))
    # Everything this file depends on (downstream)  
    descendants = list(nx.descendants(G, target_node))
    
    return {
        "file": file,
        "if_you_change_this": {
            "files_that_import_it": [
                n for n in ancestors
            ],
            "count": len(ancestors)
        },
        "this_file_depends_on": {
            "files_it_imports": [
                n for n in descendants
            ],
            "count": len(descendants)
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)