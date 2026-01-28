# 🎨 Icon Setup Guide - Material Design Icons

**Version:** 1.0
**Erstellt:** 2026-01-28

---

## 📍 Icon-Quellen

**Material Design Icons Verzeichnis:**
```
D:\03_Git\01_Global\01_GlobalDoku\google_material-design-icons-master\png\
```

**Ziel-Verzeichnis:**
```
OrderPilot-AI\src\ui\icons\
```

---

## 📋 Benötigte Icons

### Variable Reference Popup (9 Icons)

| Icon | Material Name | Pfad |
|------|---------------|------|
| search_white.png | search | action/search/materialicons/24dp/1x/baseline_search_black_24dp.png |
| copy_white.png | content_copy | content/content_copy/materialicons/24dp/1x/baseline_content_copy_black_24dp.png |
| refresh_white.png | refresh | navigation/refresh/materialicons/24dp/1x/baseline_refresh_black_24dp.png |
| save_white.png | save | content/save/materialicons/24dp/1x/baseline_save_black_24dp.png |
| download_white.png | file_download | file/file_download/materialicons/24dp/1x/baseline_file_download_black_24dp.png |
| chevron_down_white.png | expand_more | navigation/expand_more/materialicons/24dp/1x/baseline_expand_more_black_24dp.png |
| chevron_up_white.png | expand_less | navigation/expand_less/materialicons/24dp/1x/baseline_expand_less_black_24dp.png |
| close_white.png | close | navigation/close/materialicons/24dp/1x/baseline_close_black_24dp.png |
| filter_white.png | filter_list | content/filter_list/materialicons/24dp/1x/baseline_filter_list_black_24dp.png |

### Variable Manager (5 Icons)

| Icon | Material Name | Pfad |
|------|---------------|------|
| add_white.png | add | content/add/materialicons/24dp/1x/baseline_add_black_24dp.png |
| edit_white.png | edit | image/edit/materialicons/24dp/1x/baseline_edit_black_24dp.png |
| delete_white.png | delete | action/delete/materialicons/24dp/1x/baseline_delete_black_24dp.png |
| import_white.png | upload | file/upload/materialicons/24dp/1x/baseline_upload_black_24dp.png |
| export_white.png | file_download | file/file_download/materialicons/24dp/1x/baseline_file_download_black_24dp.png |

### CEL Editor (6 Icons)

| Icon | Material Name | Pfad |
|------|---------------|------|
| code_white.png | code | action/code/materialicons/24dp/1x/baseline_code_black_24dp.png |
| play_white.png | play_arrow | av/play_arrow/materialicons/24dp/1x/baseline_play_arrow_black_24dp.png |
| check_white.png | check | navigation/check/materialicons/24dp/1x/baseline_check_black_24dp.png |
| error_white.png | error | alert/error/materialicons/24dp/1x/baseline_error_black_24dp.png |
| warning_white.png | warning | alert/warning/materialicons/24dp/1x/baseline_warning_black_24dp.png |
| info_white.png | info | action/info/materialicons/24dp/1x/baseline_info_black_24dp.png |

**Total:** 20 Icons

---

## 🛠️ Option 1: Python Script mit Pillow (Automatisch)

### Installation

```bash
# In WSL
pip install Pillow
```

### Ausführung

```bash
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
python3 scripts/convert_icons_to_white.py
```

**Output:**
```
============================================================
Icon Converter - Material Design → White + Transparent
============================================================

📁 Destination: src/ui/icons

🔧 Processing: search_white
   Source: action/search/materialicons/24dp/1x/baseline_search_black_24dp.png
✅ Converted: search_white.png

... (20 icons total)

============================================================
Summary:
  ✅ Success: 20/20
  ❌ Failed:  0/20
============================================================

🎉 All icons converted successfully!
```

---

## 🛠️ Option 2: ImageMagick (Command Line)

### Installation (Windows)

Download: https://imagemagick.org/script/download.php#windows

### Konvertierung (Batch)

```bash
# Im Icon-Verzeichnis (D:\03_Git\01_Global\01_GlobalDoku\google_material-design-icons-master\png)

# Beispiel: search Icon
magick convert action/search/materialicons/24dp/1x/baseline_search_black_24dp.png ^
  -negate ^
  -fuzz 10% -transparent black ^
  D:\03_GIT\02_Python\07_OrderPilot-AI\src\ui\icons\search_white.png
```

**Batch-Script erstellen:**

Speichere als `convert_icons.bat`:

```batch
@echo off
setlocal enabledelayedexpansion

set SOURCE=D:\03_Git\01_Global\01_GlobalDoku\google_material-design-icons-master\png
set DEST=D:\03_GIT\02_Python\07_OrderPilot-AI\src\ui\icons

REM Create destination directory
if not exist "%DEST%" mkdir "%DEST%"

REM Convert each icon
echo Converting icons...

magick convert "%SOURCE%\action\search\materialicons\24dp\1x\baseline_search_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\search_white.png"
magick convert "%SOURCE%\content\content_copy\materialicons\24dp\1x\baseline_content_copy_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\copy_white.png"
magick convert "%SOURCE%\navigation\refresh\materialicons\24dp\1x\baseline_refresh_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\refresh_white.png"
magick convert "%SOURCE%\content\save\materialicons\24dp\1x\baseline_save_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\save_white.png"
magick convert "%SOURCE%\file\file_download\materialicons\24dp\1x\baseline_file_download_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\download_white.png"
magick convert "%SOURCE%\navigation\expand_more\materialicons\24dp\1x\baseline_expand_more_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\chevron_down_white.png"
magick convert "%SOURCE%\navigation\expand_less\materialicons\24dp\1x\baseline_expand_less_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\chevron_up_white.png"
magick convert "%SOURCE%\navigation\close\materialicons\24dp\1x\baseline_close_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\close_white.png"
magick convert "%SOURCE%\content\filter_list\materialicons\24dp\1x\baseline_filter_list_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\filter_white.png"
magick convert "%SOURCE%\content\add\materialicons\24dp\1x\baseline_add_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\add_white.png"
magick convert "%SOURCE%\image\edit\materialicons\24dp\1x\baseline_edit_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\edit_white.png"
magick convert "%SOURCE%\action\delete\materialicons\24dp\1x\baseline_delete_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\delete_white.png"
magick convert "%SOURCE%\file\upload\materialicons\24dp\1x\baseline_upload_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\import_white.png"
magick convert "%SOURCE%\action\code\materialicons\24dp\1x\baseline_code_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\code_white.png"
magick convert "%SOURCE%\av\play_arrow\materialicons\24dp\1x\baseline_play_arrow_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\play_white.png"
magick convert "%SOURCE%\navigation\check\materialicons\24dp\1x\baseline_check_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\check_white.png"
magick convert "%SOURCE%\alert\error\materialicons\24dp\1x\baseline_error_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\error_white.png"
magick convert "%SOURCE%\alert\warning\materialicons\24dp\1x\baseline_warning_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\warning_white.png"
magick convert "%SOURCE%\action\info\materialicons\24dp\1x\baseline_info_black_24dp.png" -negate -fuzz 10%% -transparent black "%DEST%\info_white.png"

echo Done! Icons saved to %DEST%
pause
```

**Ausführen:**
```bash
convert_icons.bat
```

---

## 🛠️ Option 3: Manuell (Photoshop/GIMP)

1. **Öffne Icon in GIMP/Photoshop**
2. **Invertiere Farben** (Schwarz → Weiß)
   - GIMP: Colors → Invert
   - Photoshop: Image → Adjustments → Invert (Ctrl+I)
3. **Setze Transparenz**
   - GIMP: Colors → Color to Alpha (wähle weiß)
   - Photoshop: Magic Wand → Select white → Delete
4. **Exportiere als PNG** mit Alpha-Kanal
5. **Speichere in:** `src/ui/icons/<name>_white.png`

---

## 📂 Icon-Verzeichnis Struktur

```
src/ui/icons/
├── search_white.png          # 24x24, weiß, transparent
├── copy_white.png
├── refresh_white.png
├── save_white.png
├── download_white.png
├── chevron_down_white.png
├── chevron_up_white.png
├── close_white.png
├── filter_white.png
├── add_white.png
├── edit_white.png
├── delete_white.png
├── import_white.png
├── export_white.png
├── code_white.png
├── play_white.png
├── check_white.png
├── error_white.png
├── warning_white.png
└── info_white.png
```

---

## 🎨 Icon Usage in Code

### QSS Stylesheet

```python
# Icon in Button
QPushButton#copy_btn {{
    background: transparent;
    border: none;
    image: url(:/icons/copy_white.png);  # Qt Resource System
    width: 24px;
    height: 24px;
}}
```

### Python Code

```python
from PyQt6.QtGui import QIcon
from pathlib import Path

ICONS_DIR = Path("src/ui/icons")

# Load icon
copy_icon = QIcon(str(ICONS_DIR / "copy_white.png"))

# Use in button
copy_btn = QPushButton()
copy_btn.setIcon(copy_icon)
copy_btn.setIconSize(QSize(24, 24))
```

### Qt Resource System (Optional)

**1. Erstelle `icons.qrc`:**

```xml
<RCC>
  <qresource prefix="/icons">
    <file>src/ui/icons/search_white.png</file>
    <file>src/ui/icons/copy_white.png</file>
    <file>src/ui/icons/refresh_white.png</file>
    <!-- ... alle Icons ... -->
  </qresource>
</RCC>
```

**2. Kompiliere:**

```bash
pyside6-rcc icons.qrc -o src/ui/icons_rc.py
```

**3. Import:**

```python
import src.ui.icons_rc  # Registriert alle Icons

# Nutze mit :/icons/ prefix
icon = QIcon(":/icons/copy_white.png")
```

---

## ✅ Verifikation

Nach Konvertierung prüfen:

1. **Icon-Größe:** 24x24 Pixel ✅
2. **Farbe:** Weiß (#FFFFFF) ✅
3. **Hintergrund:** Transparent (Alpha-Kanal) ✅
4. **Format:** PNG ✅
5. **Dateigröße:** < 2KB pro Icon ✅

**Test in Code:**

```python
from PIL import Image

icon = Image.open("src/ui/icons/search_white.png")
print(f"Size: {icon.size}")        # (24, 24)
print(f"Mode: {icon.mode}")        # RGBA
print(f"Has Alpha: {icon.mode == 'RGBA'}")  # True
```

---

## 🚀 Next Steps

1. ✅ **Icons konvertieren** (wähle Option 1, 2 oder 3)
2. ✅ **Icons in `src/ui/icons/` kopieren**
3. ✅ **In Code einbinden** (siehe "Icon Usage in Code")
4. ✅ **Testen** (Icons im UI sichtbar?)

---

**Erstellt:** 2026-01-28
**Status:** 📋 Ready for Execution
**Empfehlung:** Option 1 (Python Script) für automatische Batch-Konvertierung
