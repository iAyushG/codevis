import time
from codevis.parser import analyze_repo
from codevis.git_miner import get_git_stats

print("Testing JS parser on express...")
start = time.time()
dep_data = analyze_repo('C:\\testprojects\\express')
print(f"Done in {time.time()-start:.2f}s")
print(f"Files found: {dep_data['summary']['total_files']}")
print(f"Dependencies: {dep_data['summary']['total_dependencies']}")
print(f"Languages: {dep_data['summary']['languages']}")

print("\nTop 10 most connected files:")
from collections import defaultdict
incoming = defaultdict(int)
for edge in dep_data['edges']:
    incoming[edge['target']] += 1

top = sorted(incoming.items(), key=lambda x: x[1], reverse=True)[:10]
for filepath, count in top:
    label = dep_data['nodes'][[n['id'] for n in dep_data['nodes']].index(filepath)]['label']
    print(f"  {count} imports <- {label}")