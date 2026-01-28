# 🎨 Icon Conversion Guide

**Status:** 20/20 icons copied (black) → Need white conversion
**Goal:** Convert black Material Design icons to white with transparent background

---

## 🚀 Quick Start (Choose One Method)

### Method 1: Windows (Easiest)

**Just double-click:**
```
scripts\CONVERT_ICONS.bat
```

This will:
1. Auto-detect available tools (ImageMagick or Python+Pillow)
2. Convert all 20 icons automatically
3. Show progress and summary

---

### Method 2: PowerShell (Windows)

```powershell
cd D:\03_GIT\02_Python\07_OrderPilot-AI
powershell -ExecutionPolicy Bypass -File scripts\convert_icons_to_white.ps1
```

---

### Method 3: WSL/Linux

```bash
# Install ImageMagick first
sudo apt-get update && sudo apt-get install imagemagick

# Run conversion
./scripts/convert_icons_to_white.sh
```

---

### Method 4: Python Script

```bash
# Install Pillow first
pip install Pillow  # or: pip3 install --user Pillow

# Run conversion
python scripts/convert_icons_to_white.py
```

---

### Method 5: Manual (GIMP/Photoshop)

For each icon in `src/ui/icons/*_black.png`:

1. Open in GIMP or Photoshop
2. **Invert colors:** Colors → Invert (Ctrl+I)
3. **Make transparent:** Colors → Color to Alpha → Select white
4. **Export:** File → Export As → `<name>_white.png`
5. Save to: `src/ui/icons/<name>_white.png`

---

## 📊 Icon List (20 Total)

### Variable Reference Popup (9 icons)
- search_white.png
- copy_white.png
- refresh_white.png
- save_white.png
- download_white.png
- chevron_down_white.png
- chevron_up_white.png
- close_white.png
- filter_white.png

### Variable Manager (5 icons)
- add_white.png
- edit_white.png
- delete_white.png
- import_white.png
- export_white.png

### CEL Editor (6 icons)
- code_white.png
- play_white.png
- check_white.png
- error_white.png
- warning_white.png
- info_white.png

---

## 🔧 Troubleshooting

### "ImageMagick not found"
**Windows:**
1. Download: https://imagemagick.org/script/download.php#windows
2. Install with "Add to PATH" option checked
3. Restart terminal and try again

**WSL/Linux:**
```bash
sudo apt-get update
sudo apt-get install imagemagick
```

### "Python module 'PIL' not found"
```bash
pip install Pillow
# or for system Python:
pip3 install --user Pillow
```

### "Permission denied" (WSL)
```bash
chmod +x scripts/convert_icons_to_white.sh
./scripts/convert_icons_to_white.sh
```

---

## ✅ Verification

After conversion, check that you have:

```
src/ui/icons/
├── search_white.png  (24x24, white, transparent)
├── copy_white.png    (24x24, white, transparent)
├── ...               (18 more)
└── info_white.png    (24x24, white, transparent)
```

**Test in Python:**
```python
from PIL import Image

icon = Image.open("src/ui/icons/search_white.png")
print(f"Size: {icon.size}")        # (24, 24)
print(f"Mode: {icon.mode}")        # RGBA
print(f"Has Alpha: {icon.mode == 'RGBA'}")  # True
```

---

## 📁 Available Scripts

| Script | Platform | Requirements |
|--------|----------|--------------|
| `CONVERT_ICONS.bat` | Windows | Double-click (auto-detects tools) |
| `convert_icons_to_white.ps1` | Windows | PowerShell (auto-detects tools) |
| `convert_icons_to_white.bat` | Windows | ImageMagick |
| `convert_icons_to_white.sh` | WSL/Linux | ImageMagick |
| `convert_icons_to_white.py` | Any | Python + Pillow |
| `convert_icons_helper.py` | Any | Python (detects tools) |

---

## 🎯 Next Steps After Conversion

Once icons are converted:

1. ✅ Delete black icons (optional):
   ```bash
   rm src/ui/icons/*_black.png  # WSL
   # or
   Remove-Item src\ui\icons\*_black.png  # PowerShell
   ```

2. ✅ Continue with Phase 2: CEL Integration
3. ✅ Build Variable Reference Popup UI with new icons

---

**Created:** 2026-01-28
**Status:** Ready for conversion
**See also:** `01_Projectplan/260128_Project_Variables_System/Icon_Setup_Guide.md`
