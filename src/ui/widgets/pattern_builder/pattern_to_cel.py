"""
Pattern to CEL Code Translator.

Converts visual pattern data (candles + relations) to executable CEL code.
Supports 8 candle types and 4 relation types.
"""

from typing import List, Dict, Any, Optional


class PatternToCelTranslator:
    """Translates pattern JSON to CEL code."""

    # Candle type to CEL condition mapping
    CANDLE_TYPE_CONDITIONS = {
        "bullish": "close > open",
        "bearish": "close < open",
        "doji": "abs(close - open) < (high - low) * 0.1",  # Body < 10% of range
        "hammer": "(min(open, close) - low) > (high - min(open, close)) * 2 && abs(close - open) < (high - low) * 0.3",
        "shooting_star": "(high - max(open, close)) > (max(open, close) - low) * 2 && abs(close - open) < (high - low) * 0.3",
        "spinning_top": "(high - max(open, close)) > abs(close - open) && (min(open, close) - low) > abs(close - open)",
        "marubozu_long": "close > open && (high - close) < (close - open) * 0.1 && (open - low) < (close - open) * 0.1",
        "marubozu_short": "close < open && (high - open) < (open - close) * 0.1 && (close - low) < (open - close) * 0.1"
    }

    # Relation type to CEL operator mapping
    RELATION_OPERATORS = {
        "greater": ">",
        "less": "<",
        "equal": "==",  # CEL uses == for equality
        "near": "~"  # Will be expanded to abs(a - b) < threshold
    }

    def __init__(self):
        """Initialize translator."""
        pass

    def translate(self, pattern_data: Dict[str, Any]) -> str:
        """Translate pattern data to CEL code.

        Args:
            pattern_data: Pattern JSON from PatternBuilderCanvas.get_pattern_data()

        Returns:
            CEL code string
        """
        candles = pattern_data.get("candles", [])
        relations = pattern_data.get("relations", [])

        if not candles:
            return "// No candles in pattern"

        # Build CEL conditions
        conditions = []

        # 1. Translate candle type conditions
        candle_conditions = self._translate_candles(candles)
        conditions.extend(candle_conditions)

        # 2. Translate relation conditions
        relation_conditions = self._translate_relations(relations, candles)
        conditions.extend(relation_conditions)

        # 3. Combine with AND
        if not conditions:
            return "// No valid conditions generated"

        cel_code = " &&\n".join(conditions)
        return cel_code

    def _translate_candles(self, candles: List[Dict[str, Any]]) -> List[str]:
        """Translate candle type conditions to CEL.

        Args:
            candles: List of candle dicts

        Returns:
            List of CEL condition strings
        """
        conditions = []

        for candle in candles:
            candle_type = candle.get("type", "bullish")
            index = candle.get("index", 0)

            # Get base condition for candle type
            base_condition = self.CANDLE_TYPE_CONDITIONS.get(candle_type)
            if not base_condition:
                continue

            # Adjust condition for candle index
            # index = 0 means current candle (no offset)
            # index = -1 means candle(-1) (previous)
            # index = -2 means candle(-2) (two bars back)
            if index == 0:
                # Current candle - use variables directly
                condition = base_condition
            else:
                # Historical candle - wrap in candle() function
                # Replace open/high/low/close with candle(index).property
                condition = self._apply_candle_offset(base_condition, index)

            # Add comment for readability
            comment = f"// Candle {index}: {candle_type}"
            conditions.append(f"{comment}\n{condition}")

        return conditions

    def _apply_candle_offset(self, condition: str, index: int) -> str:
        """Apply candle index offset to condition.

        Args:
            condition: Base CEL condition
            index: Candle index (negative for historical)

        Returns:
            Modified condition with candle() function
        """
        # Replace OHLC properties with candle(index).property
        replacements = {
            "open": f"candle({index}).open",
            "high": f"candle({index}).high",
            "low": f"candle({index}).low",
            "close": f"candle({index}).close"
        }

        modified = condition
        # Sort by length (longest first) to avoid partial replacements
        for prop in sorted(replacements.keys(), key=len, reverse=True):
            modified = modified.replace(prop, replacements[prop])

        return modified

    def _translate_relations(
        self,
        relations: List[Dict[str, Any]],
        candles: List[Dict[str, Any]]
    ) -> List[str]:
        """Translate relation conditions to CEL.

        Args:
            relations: List of relation dicts
            candles: List of candle dicts (for index lookup)

        Returns:
            List of CEL condition strings
        """
        conditions = []

        # Build index map for quick lookup
        candle_by_index = {c.get("index"): c for c in candles}

        for relation in relations:
            start_index = relation.get("start_candle_index")
            end_index = relation.get("end_candle_index")
            relation_type = relation.get("relation_type", "greater")
            property_name = relation.get("property", "close")  # Default to close

            if start_index is None or end_index is None:
                continue

            # Get operator
            operator = self.RELATION_OPERATORS.get(relation_type, ">")

            # Build left and right expressions
            left_expr = self._build_property_expression(start_index, property_name)
            right_expr = self._build_property_expression(end_index, property_name)

            # Special handling for "near" (~) operator
            if relation_type == "near":
                # Convert to: abs(left - right) < threshold
                threshold = 0.01  # 1% threshold
                condition = f"abs({left_expr} - {right_expr}) < ({left_expr} * {threshold})"
            else:
                # Standard comparison
                condition = f"{left_expr} {operator} {right_expr}"

            # Add comment
            comment = f"// Relation: candle({start_index}).{property_name} {relation_type} candle({end_index}).{property_name}"
            conditions.append(f"{comment}\n{condition}")

        return conditions

    def _build_property_expression(self, index: int, property_name: str) -> str:
        """Build CEL expression for candle property access.

        Args:
            index: Candle index
            property_name: Property name (open, high, low, close)

        Returns:
            CEL expression string
        """
        if index == 0:
            # Current candle
            return property_name
        else:
            # Historical candle
            return f"candle({index}).{property_name}"

    def generate_with_comments(self, pattern_data: Dict[str, Any]) -> str:
        """Generate CEL code with detailed comments.

        Args:
            pattern_data: Pattern JSON

        Returns:
            CEL code with comments and structure
        """
        candles = pattern_data.get("candles", [])
        relations = pattern_data.get("relations", [])
        metadata = pattern_data.get("metadata", {})

        lines = []

        # Header comment
        lines.append("// Pattern-generated CEL Code")
        lines.append(f"// Candles: {metadata.get('candle_count', len(candles))}")
        lines.append(f"// Relations: {metadata.get('relation_count', len(relations))}")
        lines.append("")

        # Generate code
        cel_code = self.translate(pattern_data)
        lines.append(cel_code)

        return "\n".join(lines)

    def generate_entry_workflow(self, pattern_data: Dict[str, Any]) -> str:
        """Generate entry workflow CEL code.

        Args:
            pattern_data: Pattern JSON

        Returns:
            Entry workflow CEL code
        """
        # Entry workflow: pattern must be true AND additional entry conditions
        pattern_code = self.translate(pattern_data)

        entry_code = f"""// Entry Workflow - Pattern + Entry Conditions
// Pattern conditions
({pattern_code}) &&
// Additional entry conditions
regime == "TREND" &&
!is_trade_open()"""

        return entry_code

    def generate_exit_workflow(self, pattern_data: Dict[str, Any]) -> str:
        """Generate exit workflow CEL code.

        Args:
            pattern_data: Pattern JSON

        Returns:
            Exit workflow CEL code
        """
        # Exit workflow: inverse pattern or stop conditions
        exit_code = """// Exit Workflow - Stop/Target conditions
is_trade_open() && (
  tp_hit() ||
  stop_hit_long() ||
  stop_hit_short()
)"""

        return exit_code

    def validate_pattern(self, pattern_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate pattern data before translation.

        Args:
            pattern_data: Pattern JSON

        Returns:
            (is_valid, error_message)
        """
        candles = pattern_data.get("candles", [])
        relations = pattern_data.get("relations", [])

        # Check if pattern has candles
        if not candles:
            return False, "Pattern has no candles"

        # Check candle types
        for candle in candles:
            candle_type = candle.get("type")
            if candle_type not in self.CANDLE_TYPE_CONDITIONS:
                return False, f"Unknown candle type: {candle_type}"

        # Check relation types
        for relation in relations:
            relation_type = relation.get("relation_type")
            if relation_type not in self.RELATION_OPERATORS:
                return False, f"Unknown relation type: {relation_type}"

        return True, ""

    def get_candle_types(self) -> List[str]:
        """Get list of supported candle types.

        Returns:
            List of candle type names
        """
        return list(self.CANDLE_TYPE_CONDITIONS.keys())

    def get_relation_types(self) -> List[str]:
        """Get list of supported relation types.

        Returns:
            List of relation type names
        """
        return list(self.RELATION_OPERATORS.keys())
