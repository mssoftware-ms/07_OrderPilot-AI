import os

search_terms = ["evaluate() called", "trigger_regime_analysis"]
root_dir = r"d:\03_Git\02_Python\07_OrderPilot-AI\src"

print(f"Searching in {root_dir}...")

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for term in search_terms:
                        if term in content:
                            print(f"[FOUND] {term} in {path}")
                            # Print context
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if term in line:
                                    print(f"  Line {i+1}: {line.strip()}")
            except Exception:
                pass
