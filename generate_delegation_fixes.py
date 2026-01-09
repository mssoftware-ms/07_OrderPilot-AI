#!/usr/bin/env python3
"""Generate delegation method fixes automatically.

This script analyzes the bugs found by find_delegation_bugs.py and generates
code snippets to fix missing delegation methods.
"""

import re
from pathlib import Path
from collections import defaultdict


# Parent connection patterns from smart scanner
PARENT_CONNECTIONS = {
    "src/ui/widgets/bitunix_trading/bitunix_trading_widget.py": [
        ("_on_quantity_changed", "self._order_handler.on_quantity_changed"),
        ("_on_price_changed", "self._order_handler.on_price_changed"),
        ("_on_investment_changed", "self._order_handler.on_investment_changed"),
        ("_on_leverage_changed", "self._order_handler.on_leverage_changed"),
        ("_on_buy_clicked", "self._order_handler.on_buy_clicked"),
        ("_on_sell_clicked", "self._order_handler.on_sell_clicked"),
        ("_load_positions", "self._positions_manager._load_positions"),
        ("_delete_selected_row", "self._positions_manager.delete_selected_row"),
    ],
    "src/ui/widgets/chart_mixins/toolbar_mixin.py": [
        ("_on_load_chart", "self._toolbar_row1.on_load_chart"),
        ("_on_refresh", "self._toolbar_row1.on_refresh"),
        ("_toggle_live_stream", "self._toolbar_row2.toggle_live_stream"),
        ("_clear_all_markers", "self._toolbar_row2.clear_all_markers"),
        ("_clear_zones_with_js", "self._toolbar_row2.clear_zones_with_js"),
        ("_clear_lines_with_js", "self._toolbar_row2.clear_lines_with_js"),
        ("_clear_all_drawings", "self._toolbar_row2.clear_all_drawings"),
        ("_clear_all_markings", "self._toolbar_row2.clear_all_markings"),
    ],
    "src/ui/widgets/chart_window_mixins/bot_ui_control_mixin.py": [
        ("_update_bot_display", "self._widgets_helper.update_bot_display"),
        ("_on_bot_start_clicked", "self._handlers_helper.on_bot_start_clicked"),
        ("_on_bot_stop_clicked", "self._handlers_helper.on_bot_stop_clicked"),
        ("_on_bot_settings_clicked", "self._settings_helper.on_bot_settings_clicked"),
    ],
}


def generate_delegation_method(method_name: str, helper_call: str, is_async: bool = False) -> str:
    """Generate code for a delegation method."""

    # Determine if it's a simple value change handler or an action handler
    if method_name.startswith("_on_") and ("_changed" in method_name or "_clicked" in method_name):
        # Event handler - needs parameter
        if "_changed" in method_name:
            param_name = "value"
            param_type = "float" if "quantity" in method_name or "price" in method_name or "investment" in method_name else "int" if "leverage" in method_name else "str"
            params = f"{param_name}: {param_type}"
            call_args = f"({param_name})"
        elif "_clicked" in method_name:
            params = ""
            call_args = "()"
        else:
            params = "*args, **kwargs"
            call_args = "(*args, **kwargs)"
    else:
        # Generic delegation
        params = "*args, **kwargs"
        call_args = "(*args, **kwargs)"

    # Extract helper attribute from helper_call
    helper_attr = helper_call.split('.')[0].replace('self.', '')

    # Generate method
    lines = []

    if is_async:
        lines.append(f"    @qasync.asyncSlot()")
        lines.append(f"    async def {method_name}(self{', ' + params if params else ''}) -> None:")
    else:
        lines.append(f"    def {method_name}(self{', ' + params if params else ''}) -> None:")

    lines.append(f'        """Handle event - delegates to helper.')
    lines.append(f'')
    lines.append(f'        Delegates to {helper_call.replace("self.", "")}{call_args}.')
    lines.append(f'        """')
    lines.append(f'        if hasattr(self, \'{helper_attr}\') and self.{helper_attr} is not None:')

    # Call helper method
    helper_method_call = helper_call + call_args
    if is_async:
        lines.append(f'            await {helper_method_call}')
    else:
        lines.append(f'            {helper_method_call}')

    return '\n'.join(lines)


def main():
    print("=" * 80)
    print("DELEGATION METHOD CODE GENERATOR")
    print("=" * 80)

    for filepath, delegations in PARENT_CONNECTIONS.items():
        print(f"\n{'=' * 80}")
        print(f"File: {filepath}")
        print(f"{'=' * 80}\n")

        for method_name, helper_call in delegations:
            # Check if it's async (buy/sell clicks are async)
            is_async = method_name in ["_on_buy_clicked", "_on_sell_clicked"]

            code = generate_delegation_method(method_name, helper_call, is_async)
            print(code)
            print()

    print("\n" + "=" * 80)
    print("INSTRUCTIONS:")
    print("=" * 80)
    print("\n1. Copy the generated methods above")
    print("2. Add them to the respective files")
    print("3. Make sure to add 'import qasync' if async methods are used")
    print("4. Place methods in a logical section (e.g., 'Event Handlers' or 'Delegation Methods')")
    print("\nNOTE: Some methods may need parameter adjustments based on the actual")
    print("      signature of the helper method. Check the helper class implementation.")


if __name__ == "__main__":
    main()
