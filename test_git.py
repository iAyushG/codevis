from codevis.git_miner import get_git_stats
import json
import time

start = time.time()
r = get_git_stats('C:\\testprojects\\requests')
elapsed = time.time() - start

print(f'Time taken: {elapsed:.2f} seconds')
print(f'Files tracked: {r["summary"]["total_files_tracked"]}')
print(f'Hottest file: {r["summary"]["hottest_file"]}')
print(f'Coupled pairs: {r["summary"]["coupled_pairs"]}')

print('\nTOP 10 HOTSPOTS:')
top = sorted(r['churn'].items(), key=lambda x: x[1]['changes'], reverse=True)[:10]
for f, v in top:
    print(f"  {v['risk_score']} | {v['changes']} changes | {f}")