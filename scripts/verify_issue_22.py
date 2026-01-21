import os
import sys

def verify_issue_22():
    print("Verifying Issue 22 Fixes...")
    
    # Check icons
    icons_dir = r"d:\03_Git\02_Python\07_OrderPilot-AI\src\ui\assets\icons"
    live_icon = os.path.join(icons_dir, "live.png")
    indicators_icon = os.path.join(icons_dir, "indicators.png")
    
    if os.path.exists(live_icon):
        print(f"SUCCESS: live.png found at {live_icon}")
    else:
        print(f"FAILURE: live.png not found at {live_icon}")
        
    if os.path.exists(indicators_icon):
        print(f"SUCCESS: indicators.png found at {indicators_icon}")
    else:
        print(f"FAILURE: indicators.png not found at {indicators_icon}")
        
    # Check code
    mixin_file = r"d:\03_Git\02_Python\07_OrderPilot-AI\src\ui\widgets\chart_mixins\toolbar_mixin_row1.py"
    try:
        with open(mixin_file, "r", encoding="utf-8") as f:
            content = f.read()
            if 'self.parent.indicators_button.setIcon(get_icon("indicators"))' in content:
                print("SUCCESS: Code updated to use 'indicators' icon in toolbar_mixin_row1.py")
            else:
                print("FAILURE: Code NOT updated in toolbar_mixin_row1.py")
                # print snippet
                print("Snippet around line 116:")
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if "self.parent.indicators_button = QPushButton" in line:
                         print(f"{i+1}: {line}")
                         if i+1 < len(lines): print(f"{i+2}: {lines[i+1]}")
    except Exception as e:
        print(f"FAILURE: Could not read file: {e}")

if __name__ == "__main__":
    verify_issue_22()
