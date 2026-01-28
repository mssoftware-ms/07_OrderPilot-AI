#!/bin/bash
# Icon Conversion Script - Black to White with Transparent Background
# Requires: ImageMagick installed (sudo apt-get install imagemagick)

ICONS_DIR="src/ui/icons"

echo "========================================="
echo "Icon Color Converter - Black to White"
echo "========================================="
echo ""

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ ERROR: ImageMagick not found!"
    echo ""
    echo "Please install ImageMagick:"
    echo "  sudo apt-get install imagemagick"
    echo ""
    exit 1
fi

echo "✅ ImageMagick found. Converting icons..."
echo ""

# List of icons to convert
ICONS=(
    "search" "copy" "refresh" "save" "download"
    "chevron_down" "chevron_up" "close" "filter"
    "add" "edit" "delete" "import" "export"
    "code" "play" "check" "error" "warning" "info"
)

SUCCESS=0
FAILED=0

for icon in "${ICONS[@]}"; do
    src="${ICONS_DIR}/${icon}_black.png"
    dest="${ICONS_DIR}/${icon}_white.png"

    if [ -f "$src" ]; then
        echo "Converting ${icon}..."
        convert "$src" -negate -fuzz 10% -transparent black "$dest"

        if [ -f "$dest" ]; then
            echo "  ✅ Created: ${icon}_white.png"
            ((SUCCESS++))
        else
            echo "  ❌ Failed: ${icon}_white.png"
            ((FAILED++))
        fi
    else
        echo "  ❌ Source not found: ${icon}_black.png"
        ((FAILED++))
    fi
done

echo ""
echo "========================================="
echo "Summary:"
echo "  ✅ Success: ${SUCCESS}/20"
echo "  ❌ Failed:  ${FAILED}/20"
echo "========================================="
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All icons converted successfully!"
    echo ""
    echo "You can delete black icons if you want:"
    echo "  rm ${ICONS_DIR}/*_black.png"
else
    echo "⚠️  Some icons failed to convert."
    echo "Check errors above."
fi

echo ""
