
import os

def check_file_content(filepath, unwanted_content=None, expected_content_list=None):
    if not os.path.exists(filepath):
        print(f"FAILED: File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    success = True
    if unwanted_content:
        if unwanted_content in content:
            print(f"FAILED: Found unwanted content '{unwanted_content}' in {filepath}")
            success = False
        else:
            print(f"PASSED: Unwanted content not found in {filepath}")

    if expected_content_list:
        for expected in expected_content_list:
            if expected in content:
                print(f"PASSED: Found expected content segment in {filepath}")
            else:
                print(f"FAILED: Missing expected content segment in {filepath}:\n'{expected}'")
                success = False
    return success

def verify_issue_26():
    print("Verifying Issue 26 changes...")
    all_passed = True
    
    # Check 1: chart_js_template.html
    template_path = r"d:\03_Git\02_Python\07_OrderPilot-AI\src\ui\widgets\chart_js_template.html"
    if not check_file_content(template_path, unwanted_content="Ready v4 - waiting for data..."):
        all_passed = False
        
    # Check 2: embedded_tradingview_chart_ui_mixin.py
    # We want to ensure toolbar is added BEFORE ohlc_info_label
    # This is hard to regex exactly without multiline complexity, but we can check if the new order exists
    mixin_path = r"d:\03_Git\02_Python\07_OrderPilot-AI\src\ui\widgets\embedded_tradingview_chart_ui_mixin.py"
    expected_order_snippet = """        # Toolbar (from ToolbarMixin) - Two rows
        toolbar1, toolbar2 = self._create_toolbar()
        self.toolbar_row1 = toolbar1
        self.toolbar_row2 = toolbar2
        layout.addWidget(toolbar1)
        layout.addWidget(toolbar2)

        # Issue #26: OHLC Info Label (unter Toolbar)
        self.ohlc_info_label = QLabel("O -- | H -- | L -- | C -- | -- % | V --")"""
    
    # Normalize line endings just in case
    if not check_file_content(mixin_path, expected_content_list=[expected_order_snippet.replace('\r\n', '\n')]):
         # Try flexible check if exact match fails due to whitespace
         with open(mixin_path, 'r') as f:
             content = f.read()
         if "layout.addWidget(toolbar2)" in content and 'self.ohlc_info_label = QLabel("O -- | H -- | L -- | C -- | -- % | V --")' in content:
             t2_idx = content.find("layout.addWidget(toolbar2)")
             lbl_idx = content.find('self.ohlc_info_label = QLabel("O -- | H -- | L -- | C -- | -- % | V --")')
             if t2_idx < lbl_idx:
                 print("PASSED: Toolbar appears before OHLC label (logic check)")
             else:
                 print("FAILED: Toolbar appears AFTER OHLC label")
                 all_passed = False
         else:
             all_passed = False

    # Check 3: chart_stats_labels_mixin.py
    stats_path = r"d:\03_Git\02_Python\07_OrderPilot-AI\src\ui\widgets\chart_mixins\chart_stats_labels_mixin.py"
    if not check_file_content(stats_path, expected_content_list=['ZoneInfo("Europe/Berlin")']):
        all_passed = False

    if all_passed:
        print("\nAll checks passed for Issue 26!")
    else:
        print("\nSome checks failed for Issue 26.")

if __name__ == "__main__":
    verify_issue_26()
