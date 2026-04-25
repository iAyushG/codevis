import subprocess
from collections import defaultdict


def get_churn(repo_path: str) -> dict[str, int]:
    """Count how many times each file has changed in git history"""
    try:
        result = subprocess.run(
            ['git', 'log', '--name-only', '--format='],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        churn = defaultdict(int)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                churn[line] += 1
        return dict(churn)

    except Exception:
        return {}


def get_cochange(repo_path: str) -> list[dict]:
    """Find files that always change together in the same commit"""
    try:
        result = subprocess.run(
            ['git', 'log', '--name-only', '--format=COMMIT'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        commits = []
        current = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line == 'COMMIT':
                if current:
                    commits.append(current)
                current = []
            elif line:
                current.append(line)
        if current:
            commits.append(current)

        pair_counts = defaultdict(int)
        for files in commits:
            files = sorted(set(files))
            for i in range(len(files)):
                for j in range(i + 1, len(files)):
                    pair_counts[(files[i], files[j])] += 1

        results = []
        for (f1, f2), count in pair_counts.items():
            if count >= 2:
                results.append({
                    "file1": f1,
                    "file2": f2,
                    "times_together": count
                })

        return sorted(results, key=lambda x: x["times_together"], reverse=True)

    except Exception:
        return []


def get_git_stats(repo_path: str) -> dict:
    """Get full git intelligence for a repo — churn + co-change"""
    churn = get_churn(repo_path)
    cochange = get_cochange(repo_path)

    if churn:
        max_churn = max(churn.values())
        churn_scored = {
            f: {
                "changes": count,
                "risk_score": round(count / max_churn, 2)
            }
            for f, count in churn.items()
        }
    else:
        churn_scored = {}

    return {
        "churn": churn_scored,
        "cochange": cochange,
        "summary": {
            "total_files_tracked": len(churn),
            "hottest_file": max(churn, key=churn.get) if churn else None,
            "coupled_pairs": len(cochange)
        }
    }