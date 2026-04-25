import sys
import json
import time
from codevis.git_miner import get_git_stats
from codevis.parser import analyze_repo

def analyze(repo_path: str):
    print(f"Analyzing {repo_path}...")
    
    print("  Running git analysis...")
    start = time.time()
    git_data = get_git_stats(repo_path)
    print(f"  Done in {time.time()-start:.2f}s — {git_data['summary']['total_files_tracked']} files tracked")
    
    print("  Running dependency analysis...")
    start = time.time()
    dep_data = analyze_repo(repo_path)
    print(f"  Done in {time.time()-start:.2f}s — {dep_data['summary']['total_files']} files, {dep_data['summary']['total_dependencies']} edges")
    
    # Merge churn scores into dependency nodes
    for node in dep_data['nodes']:
        label = node['label'].replace('\\', '/')
        churn_info = git_data['churn'].get(label, {})
        node['changes'] = churn_info.get('changes', 0)
        node['risk_score'] = churn_info.get('risk_score', 0)
    
    result = {
        "repo": repo_path,
        "summary": {
            "total_files": dep_data['summary']['total_files'],
            "total_dependencies": dep_data['summary']['total_dependencies'],
            "total_files_tracked_by_git": git_data['summary']['total_files_tracked'],
            "hottest_file": git_data['summary']['hottest_file'],
            "coupled_pairs": git_data['summary']['coupled_pairs']
        },
        "nodes": dep_data['nodes'],
        "edges": dep_data['edges'],
        "churn": git_data['churn'],
        "cochange": git_data['cochange']
    }
    
    output_file = 'analysis.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nSaved to {output_file}")
    print(f"Total files: {result['summary']['total_files']}")
    print(f"Total dependencies: {result['summary']['total_dependencies']}")
    print(f"Hottest file: {result['summary']['hottest_file']}")
    print(f"\nTop 5 hotspots:")
    top = sorted(git_data['churn'].items(), key=lambda x: x[1]['changes'], reverse=True)[:5]
    for f, v in top:
        print(f"  {v['risk_score']} | {v['changes']} changes | {f}")

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else input("Enter repo path: ")
    analyze(repo)