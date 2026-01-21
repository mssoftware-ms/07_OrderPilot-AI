"""
Setup Icons Script.

Copies icons from the provided Google Material Design path to the project assets.
Handles searching for files if precise paths vary slightly.
Recolors icons to WHITE (with transparency) using Pillow.
"""
import os
import shutil
import glob
from pathlib import Path
try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed. Icons will not be recolored to white.")

SOURCE_ROOT = Path("/mnt/d/03_GIT/01_Global/01_GlobalDoku/google_material-design-icons-master/png")
DEST_ROOT = Path("src/ui/assets/icons")

# Map of internal name -> (category_hint, source_name)
ICON_MAP = {
    "chart":       ("editor", "show_chart"),
    "order":       ("action", "assignment"),
    "settings":    ("action", "settings"),
    "connect":     ("action", "power_settings_new"),
    "disconnect":  ("action", "power_off"),
    "refresh":     ("navigation", "refresh"),
    "watchlist":   ("action", "list"),
    "data_source": ("device", "storage"),
    "backtest":    ("action", "history"),
    "portfolio":   ("action", "account_balance_wallet"),
    "ai":          ("hardware", "memory"),
    "optimize":    ("action", "trending_up"),
    "zoom_all":    ("maps", "zoom_out_map"),
    "expand":      ("navigation", "fullscreen"),
    
    # Common Actions
    "start":       ("av", "play_arrow"),
    "stop":        ("av", "stop"),
    "save":        ("content", "save"),
    "load":        ("file", "folder_open"),
    "edit":        ("editor", "mode_edit"),
    "delete":      ("action", "delete"),
    "clear":       ("content", "clear"),
    "add":         ("content", "add"),
    "close":       ("navigation", "close"),
    "check":       ("navigation", "check"),
    "warning":     ("alert", "warning"),
    "info":        ("action", "info"),
    "help":        ("action", "help"),
    "auto":        ("action", "autorenew"),
}

def find_icon_path(category_hint, name):
    """Find the icon file in the source directory."""
    # 1. Try exact hint match
    # Pattern: category/name/materialicons/24dp/2x/baseline_name_black_24dp.png
    hints = [category_hint]
    
    # 2. Add other common categories as fallback
    all_categories = [d.name for d in SOURCE_ROOT.iterdir() if d.is_dir()]
    hints.extend([c for c in all_categories if c != category_hint])
    
    for category in hints:
        base_path = SOURCE_ROOT / category / name
        if not base_path.exists():
            continue
            
        # Try 24dp 2x (High DPI)
        patterns = [
            f"**/24dp/2x/baseline_{name}_black_24dp.png",
            f"**/24dp/2x/*{name}*black*.png",
            f"**/*{name}*black*.png" # Fallback
        ]
        
        for pattern in patterns:
            matches = list(base_path.glob(pattern))
            if matches:
                return matches[0]
                
    # 3. Last resort: Search anywhere
    print(f"   Deep search for {name}...")
    matches = list(SOURCE_ROOT.glob(f"**/*{name}*black*24dp.png"))
    if matches:
        return matches[0]
        
    return None

def process_and_save_icon(src_path, dest_path):
    """Copy and optionally recolor icon to white."""
    if PIL_AVAILABLE:
        try:
            with Image.open(src_path) as img:
                img = img.convert("RGBA")
                
                # Create a white image with the same alpha channel
                # Split channels
                r, g, b, a = img.split()
                
                # Create solid white image
                white = Image.new("RGB", img.size, (255, 255, 255))
                
                # Merge white with original alpha
                new_img = Image.merge("RGBA", (white.split()[0], white.split()[1], white.split()[2], a))
                
                new_img.save(dest_path, "PNG")
                return True
        except Exception as e:
            print(f"   Error processing {src_path}: {e}")
            return False
    else:
        shutil.copy2(src_path, dest_path)
        return True

def main():
    if not DEST_ROOT.exists():
        os.makedirs(DEST_ROOT)
        print(f"Created directory: {DEST_ROOT}")
        
    print(f"Processing icons from {SOURCE_ROOT}...")
    
    success_count = 0
    
    for icon_name, (category, src_name) in ICON_MAP.items():
        src_path = find_icon_path(category, src_name)
        
        if src_path:
            dest_path = DEST_ROOT / f"{icon_name}.png"
            if process_and_save_icon(src_path, dest_path):
                print(f"✅ Processed: {icon_name}.png")
                success_count += 1
            else:
                print(f"⚠️ Copy failed: {icon_name}.png")
        else:
            print(f"❌ Failed to find icon: {icon_name} (hint: {category}/{src_name})")

    print(f"\nDone. {success_count}/{len(ICON_MAP)} icons processed.")

if __name__ == "__main__":
    main()
