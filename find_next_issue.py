import os
import json
import re

issues_dir = 'issues'
files = [f for f in os.listdir(issues_dir) if f.endswith('.json')]

# Sort by number in filename if possible
def get_num(fname):
    m = re.search(r'(\d+)', fname)
    return int(m.group(1)) if m else 999999

files.sort(key=get_num)

for f in files:
    path = os.path.join(issues_dir, f)
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
            if data.get('state') == 'open':
                print(f"NEXT_OPEN_ISSUE: {f}")
                print(f"TITLE: {data.get('title')}")
                break
    except Exception as e:
        print(f"Error reading {f}: {e}")
