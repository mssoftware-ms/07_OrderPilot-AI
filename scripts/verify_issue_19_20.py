import os
import sys
from pathlib import Path
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QSizePolicy

# Add src to pythonpath
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def check_icons():
    print("\n--- Checking Icons ---")
    icons_dir = project_root / "src" / "ui" / "assets" / "icons"
    required_icons = ["chart.png", "entry_analyzer.png", "warning.png", "lightbulb.png", "refresh.png"]
    
    all_exist = True
    for icon in required_icons:
        path = icons_dir / icon
        if path.exists():
            print(f"✅ Found: {icon}")
        else:
            print(f"❌ Missing: {icon}")
            all_exist = False
    return all_exist

def check_code_content():
    print("\n--- Checking Code Content ---")
    file_path = project_root / "src" / "ui" / "widgets" / "analysis_tabs" / "ai_chat_tab.py"
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    checks = {
        "Font Size Set": "button_font.setPointSize(9)",
        "Icon Size 16": "ICON_SIZE = QSize(16, 16)",
        "Chat Expanding": "self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)",
        "Input Field Present": "self.input_field = QLineEdit()",
        "Icon chart": '"chart"',
        "Icon entry_analyzer": '"entry_analyzer"',
        "Icon warning": '"warning"',
        "Icon lightbulb": '"lightbulb"',
        "Icon refresh": 'get_icon("refresh")',
    }
    
    all_passed = True
    for check_name, string_to_find in checks.items():
        if string_to_find in content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Not Found")
            all_passed = False
            
    return all_passed

if __name__ == "__main__":
    icons_ok = check_icons()
    code_ok = check_code_content()
    
    if icons_ok and code_ok:
        print("\n✅ VERIFICATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED")
        sys.exit(1)
