import os
import glob

root = r"d:\03_Git\02_Python\07_OrderPilot-AI\src"
print(f"Searching for 'context keys:' in {root}")

for filepath in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            if "context keys:" in content:
                print(f"MATCH: {filepath}")
                for i, line in enumerate(content.splitlines()):
                    if "context keys:" in line:
                        print(f"  Line {i+1}: {line.strip()}")
    except: pass
