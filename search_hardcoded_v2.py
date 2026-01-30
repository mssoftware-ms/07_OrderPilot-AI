import os
import glob

root = r"d:\03_Git\02_Python\07_OrderPilot-AI\src"
print(f"Searching {root}")
found = []
for filepath in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            if "trigger_regime_analysis" in content or "[CEL] evaluate" in content:
                print(f"\nMATCH: {filepath}")
                lines = content.splitlines()
                for i, line in enumerate(lines):
                     if "trigger_regime_analysis" in line or "[CEL] evaluate" in line:
                         print(f"  Line {i+1}: {line.strip()[:150]}")
    except: pass
