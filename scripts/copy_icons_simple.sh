#!/bin/bash
# Simple Icon Copy Script (without color conversion)
# Icons will be copied as-is (black) and need manual conversion to white

SOURCE="/mnt/d/03_Git/01_Global/01_GlobalDoku/google_material-design-icons-master/png"
DEST="src/ui/icons"

# Create destination
mkdir -p "$DEST"

echo "📋 Copying Material Design Icons..."
echo "⚠️  Note: Icons are BLACK and need manual conversion to WHITE"
echo ""

# Copy icons (24dp baseline versions)
declare -A ICONS=(
    ["search_black"]="action/search/materialicons/24dp/1x/baseline_search_black_24dp.png"
    ["copy_black"]="content/content_copy/materialicons/24dp/1x/baseline_content_copy_black_24dp.png"
    ["refresh_black"]="navigation/refresh/materialicons/24dp/1x/baseline_refresh_black_24dp.png"
    ["save_black"]="content/save/materialicons/24dp/1x/baseline_save_black_24dp.png"
    ["download_black"]="file/file_download/materialicons/24dp/1x/baseline_file_download_black_24dp.png"
    ["chevron_down_black"]="navigation/expand_more/materialicons/24dp/1x/baseline_expand_more_black_24dp.png"
    ["chevron_up_black"]="navigation/expand_less/materialicons/24dp/1x/baseline_expand_less_black_24dp.png"
    ["close_black"]="navigation/close/materialicons/24dp/1x/baseline_close_black_24dp.png"
    ["filter_black"]="content/filter_list/materialicons/24dp/1x/baseline_filter_list_black_24dp.png"
    ["add_black"]="content/add/materialicons/24dp/1x/baseline_add_black_24dp.png"
    ["edit_black"]="image/edit/materialicons/24dp/1x/baseline_edit_black_24dp.png"
    ["delete_black"]="action/delete/materialicons/24dp/1x/baseline_delete_black_24dp.png"
    ["import_black"]="file/upload/materialicons/24dp/1x/baseline_upload_black_24dp.png"
    ["export_black"]="file/file_download/materialicons/24dp/1x/baseline_file_download_black_24dp.png"
    ["code_black"]="action/code/materialicons/24dp/1x/baseline_code_black_24dp.png"
    ["play_black"]="av/play_arrow/materialicons/24dp/1x/baseline_play_arrow_black_24dp.png"
    ["check_black"]="navigation/check/materialicons/24dp/1x/baseline_check_black_24dp.png"
    ["error_black"]="alert/error/materialicons/24dp/1x/baseline_error_black_24dp.png"
    ["warning_black"]="alert/warning/materialicons/24dp/1x/baseline_warning_black_24dp.png"
    ["info_black"]="action/info/materialicons/24dp/1x/baseline_info_black_24dp.png"
)

SUCCESS=0
FAILED=0

for icon_name in "${!ICONS[@]}"; do
    src_path="$SOURCE/${ICONS[$icon_name]}"
    dest_path="$DEST/${icon_name}.png"
    
    if [ -f "$src_path" ]; then
        cp "$src_path" "$dest_path"
        echo "✅ Copied: ${icon_name}.png"
        ((SUCCESS++))
    else
        echo "❌ Not found: ${ICONS[$icon_name]}"
        ((FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "Summary: $SUCCESS copied, $FAILED failed"
echo "=========================================="
echo ""
echo "⚠️  NEXT STEP: Convert black icons to white"
echo "   Option 1: Use convert_icons.bat (Windows + ImageMagick)"
echo "   Option 2: Manual with GIMP/Photoshop"
echo "   See: 01_Projectplan/260128_Project_Variables_System/Icon_Setup_Guide.md"
