# UI Customization & Icons

## 1. Code Changes Implemented
I have implemented the requested UI customization features:

*   **Settings > General > UI Customization**:
    *   **Button Border Color**: Color picker for button borders.
    *   **Global Font Color**: Color picker for application-wide text.
    *   **Font Family**: Dropdown to select from system installed fonts (e.g., Segoe UI, Arial).
    *   **Font Size**: Spinbox to adjust global font size (8-30px).
*   **Global Application**: Changes apply to the entire application upon saving.
*   **Exclusions**:
    *   **Kill Switch**: Retains its distinct red styling (via inline styles).
    *   **Live Data Button**: Retains its default styling (via ID exclusion `#liveDataToggle`).

## 2. Icon Set Recommendation
For a modern, flat trading icon set, I recommend **"Trading Flat" by Flaticon** or **IconScout**.

Since I cannot browse the web interactively to download files, please follow these steps:

1.  **Visit**: [Flaticon Trading Icons](https://www.flaticon.com/free-icons/trading) or [IconScout Trading Pack](https://iconscout.com/icon-pack/trading-flat).
2.  **Download**: Choose a pack that fits your style (SVG or PNG).
3.  **Place**: Extract the icons to `root/icons/` (create the folder if it doesn't exist).
4.  **Usage**: The application currently uses `src/ui/icons.py` to manage icons. You can update that file to point to your new icons if you wish to replace the built-in ones.

## 3. Verification
*   Open **Settings -> General**.
*   Scroll to **UI Customization**.
*   Change the colors and font.
*   Click **Save**. The theme should update immediately.
*   Verify that "Kill Switch" and "Live Data" buttons remain unchanged.
