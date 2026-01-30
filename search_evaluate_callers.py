import os
import glob
root = r"d:\03_Git\02_Python\07_OrderPilot-AI\src"
print(f"Searching for .evaluate( in {root}")
for filepath in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if ".evaluate(" in line and "def " not in line:
                    print(f"MATCH: {filepath}:{i+1} -> {line.strip()[:100]}")
    except: pass
