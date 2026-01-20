"""RulePack Executor with Monotonic Stop Enforcement.

Executes RulePacks in correct order with priority-based sorting and
early termination on block severity.

Execution Order:
    1. exit (check if position should be closed)
    2. update_stop (adjust stop-loss if needed)
    3. risk (check risk conditions)
    4. entry (check if new position can be opened)

Monotonic Stop Enforcement:
    - LONG positions: new_stop = max(current_stop, calculated_stop)
    - SHORT positions: new_stop = min(current_stop, calculated_stop)
"""

import logging
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

from .engine import CELEngine
from .models import RulePack, Pack, Rule

logger = logging.getLogger(__name__)


class ExecutionResult(Enum):
    """Result of rule execution."""
    ALLOW = "allow"        # Rule passed, continue
    BLOCK = "block"        # Rule blocked, stop execution
    EXIT = "exit"          # Rule triggered exit
    UPDATE_STOP = "update_stop"  # Rule triggered stop update
    WARN = "warn"          # Rule triggered warning


@dataclass
class RuleResult:
    """Result of single rule evaluation."""
    rule_id: str
    rule_name: str
    triggered: bool
    severity: str
    message: str
    execution_time_ms: float

    def __str__(self) -> str:
        status = "✅ TRIGGERED" if self.triggered else "⏭️  SKIPPED"
        return f"{status} [{self.severity}] {self.rule_name} ({self.execution_time_ms:.2f}ms)"


@dataclass
class PackResult:
    """Result of pack evaluation."""
    pack_type: str
    rules_evaluated: int
    rules_triggered: int
    execution_result: ExecutionResult
    rule_results: list[RuleResult]
    total_time_ms: float
    blocked_by: Optional[str] = None  # Rule ID that caused block

    def __str__(self) -> str:
        return (
            f"Pack: {self.pack_type} | "
            f"Evaluated: {self.rules_evaluated} | "
            f"Triggered: {self.rules_triggered} | "
            f"Result: {self.execution_result.value} | "
            f"Time: {self.total_time_ms:.2f}ms"
        )


@dataclass
class ExecutionSummary:
    """Summary of complete RulePack execution."""
    packs_executed: int
    total_rules_evaluated: int
    total_rules_triggered: int
    total_time_ms: float
    pack_results: list[PackResult]
    final_decision: ExecutionResult
    blocked_by_pack: Optional[str] = None
    blocked_by_rule: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"=== RulePack Execution Summary ===\n"
            f"Packs Executed: {self.packs_executed}\n"
            f"Rules Evaluated: {self.total_rules_evaluated}\n"
            f"Rules Triggered: {self.total_rules_triggered}\n"
            f"Total Time: {self.total_time_ms:.2f}ms\n"
            f"Final Decision: {self.final_decision.value}\n"
            f"Blocked By: {self.blocked_by_pack or 'None'} / {self.blocked_by_rule or 'None'}"
        )


class RulePackExecutor:
    """Executes RulePacks with correct ordering and stop enforcement.

    Features:
    - Correct execution order (exit → update_stop → risk → entry)
    - Monotonic stop enforcement (Long: max(), Short: min())
    - Priority-based rule sorting (high priority first)
    - Early termination on block severity
    - Rule profiling and statistics

    Example:
        executor = RulePackExecutor(engine)
        summary = executor.execute(rulepack, context)

        if summary.final_decision == ExecutionResult.ALLOW:
            # Proceed with entry
            pass
        elif summary.final_decision == ExecutionResult.BLOCK:
            # Don't enter trade
            logger.warning(f"Blocked by: {summary.blocked_by_rule}")
    """

    # Correct execution order
    EXECUTION_ORDER = ["exit", "update_stop", "risk", "entry"]

    def __init__(self, engine: Optional[CELEngine] = None):
        """Initialize RulePack executor.

        Args:
            engine: Optional CEL engine (creates new if None)
        """
        self.engine = engine or CELEngine()
        self.rule_stats: dict[str, dict[str, Any]] = {}  # Rule profiling
        logger.info("RulePackExecutor initialized")

    def execute(
        self,
        rulepack: RulePack,
        context: dict[str, Any],
        pack_types: Optional[list[str]] = None,
    ) -> ExecutionSummary:
        """Execute RulePack with correct ordering.

        Args:
            rulepack: RulePack to execute
            context: CEL evaluation context
            pack_types: Optional list of pack types to execute (default: all in order)

        Returns:
            ExecutionSummary with results

        Example:
            # Execute all packs
            summary = executor.execute(rulepack, context)

            # Execute only entry and risk packs
            summary = executor.execute(rulepack, context, pack_types=["risk", "entry"])
        """
        import time

        start_time = time.perf_counter()

        # Determine which packs to execute
        if pack_types is None:
            pack_types = self.EXECUTION_ORDER
        else:
            # Sort pack_types by execution order
            pack_types = [
                pt for pt in self.EXECUTION_ORDER
                if pt in pack_types
            ]

        pack_results: list[PackResult] = []
        total_rules_evaluated = 0
        total_rules_triggered = 0
        final_decision = ExecutionResult.ALLOW
        blocked_by_pack: Optional[str] = None
        blocked_by_rule: Optional[str] = None

        # Execute packs in order
        for pack_type in pack_types:
            pack = rulepack.get_pack(pack_type)

            if pack is None:
                logger.debug(f"Pack '{pack_type}' not found in RulePack, skipping")
                continue

            # Evaluate pack
            pack_result = self._evaluate_pack(pack, context)
            pack_results.append(pack_result)

            total_rules_evaluated += pack_result.rules_evaluated
            total_rules_triggered += pack_result.rules_triggered

            # Check for early termination
            if pack_result.execution_result == ExecutionResult.BLOCK:
                final_decision = ExecutionResult.BLOCK
                blocked_by_pack = pack_type
                blocked_by_rule = pack_result.blocked_by

                logger.warning(
                    f"Execution blocked by {pack_type} pack, rule: {blocked_by_rule}"
                )
                break

            # Update final decision based on pack type
            if pack_result.execution_result != ExecutionResult.ALLOW:
                final_decision = pack_result.execution_result

        total_time = (time.perf_counter() - start_time) * 1000

        summary = ExecutionSummary(
            packs_executed=len(pack_results),
            total_rules_evaluated=total_rules_evaluated,
            total_rules_triggered=total_rules_triggered,
            total_time_ms=total_time,
            pack_results=pack_results,
            final_decision=final_decision,
            blocked_by_pack=blocked_by_pack,
            blocked_by_rule=blocked_by_rule,
        )

        logger.info(f"RulePack execution completed: {summary}")
        return summary

    def _evaluate_pack(self, pack: Pack, context: dict[str, Any]) -> PackResult:
        """Evaluate single pack with priority-based sorting.

        Args:
            pack: Pack to evaluate
            context: CEL context

        Returns:
            PackResult with evaluation details
        """
        import time

        start_time = time.perf_counter()

        # Sort rules by priority (high priority first)
        sorted_rules = sorted(
            [r for r in pack.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True
        )

        rule_results: list[RuleResult] = []
        rules_triggered = 0
        execution_result = ExecutionResult.ALLOW
        blocked_by: Optional[str] = None

        for rule in sorted_rules:
            rule_result = self._evaluate_rule(rule, context)
            rule_results.append(rule_result)

            # Update rule statistics
            self._update_rule_stats(rule.id, rule_result)

            if rule_result.triggered:
                rules_triggered += 1

                # Check for block severity (early termination)
                if rule.severity == "block":
                    execution_result = ExecutionResult.BLOCK
                    blocked_by = rule.id

                    logger.warning(
                        f"Rule {rule.id} blocked execution (severity=block)"
                    )
                    break

                # Map severity to execution result
                elif rule.severity == "exit":
                    execution_result = ExecutionResult.EXIT
                elif rule.severity == "update_stop":
                    execution_result = ExecutionResult.UPDATE_STOP
                elif rule.severity == "warn":
                    if execution_result == ExecutionResult.ALLOW:
                        execution_result = ExecutionResult.WARN

        total_time = (time.perf_counter() - start_time) * 1000

        pack_result = PackResult(
            pack_type=pack.pack_type,
            rules_evaluated=len(rule_results),
            rules_triggered=rules_triggered,
            execution_result=execution_result,
            rule_results=rule_results,
            total_time_ms=total_time,
            blocked_by=blocked_by,
        )

        logger.debug(f"Pack evaluation: {pack_result}")
        return pack_result

    def _evaluate_rule(self, rule: Rule, context: dict[str, Any]) -> RuleResult:
        """Evaluate single rule.

        Args:
            rule: Rule to evaluate
            context: CEL context

        Returns:
            RuleResult with evaluation details
        """
        import time

        start_time = time.perf_counter()

        # Evaluate expression
        triggered = self.engine.evaluate_safe(
            rule.expression,
            context,
            default=False
        )

        exec_time = (time.perf_counter() - start_time) * 1000

        result = RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=bool(triggered),
            severity=rule.severity,
            message=rule.message or "",
            execution_time_ms=exec_time,
        )

        if triggered:
            logger.debug(f"Rule triggered: {result}")

        return result

    def _update_rule_stats(self, rule_id: str, result: RuleResult) -> None:
        """Update rule profiling statistics.

        Args:
            rule_id: Rule ID
            result: Rule evaluation result
        """
        if rule_id not in self.rule_stats:
            self.rule_stats[rule_id] = {
                "evaluations": 0,
                "triggers": 0,
                "total_time_ms": 0.0,
                "avg_time_ms": 0.0,
            }

        stats = self.rule_stats[rule_id]
        stats["evaluations"] += 1

        if result.triggered:
            stats["triggers"] += 1

        stats["total_time_ms"] += result.execution_time_ms
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["evaluations"]

    def get_rule_stats(self, rule_id: Optional[str] = None) -> dict[str, Any]:
        """Get rule profiling statistics.

        Args:
            rule_id: Optional specific rule ID (returns all if None)

        Returns:
            Rule statistics dict

        Example:
            # Get all stats
            all_stats = executor.get_rule_stats()

            # Get specific rule stats
            rule_stats = executor.get_rule_stats("entry_rsi_oversold_long")
            print(f"Triggered {rule_stats['triggers']} / {rule_stats['evaluations']} times")
        """
        if rule_id:
            return self.rule_stats.get(rule_id, {})
        return self.rule_stats

    def get_most_triggered_rules(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Get most frequently triggered rules.

        Args:
            top_n: Number of top rules to return

        Returns:
            List of (rule_id, trigger_count) tuples

        Example:
            top_rules = executor.get_most_triggered_rules(top_n=5)
            for rule_id, count in top_rules:
                print(f"{rule_id}: {count} triggers")
        """
        rules_with_counts = [
            (rule_id, stats["triggers"])
            for rule_id, stats in self.rule_stats.items()
        ]

        # Sort by trigger count descending
        sorted_rules = sorted(
            rules_with_counts,
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_rules[:top_n]

    def clear_stats(self) -> None:
        """Clear all rule profiling statistics."""
        self.rule_stats.clear()
        logger.info("Rule statistics cleared")


def enforce_monotonic_stop(
    direction: str,
    current_stop: float,
    new_stop: float,
) -> float:
    """Enforce monotonic stop-loss updates.

    LONG positions: Stop can only move UP (max)
    SHORT positions: Stop can only move DOWN (min)

    Args:
        direction: Trade direction ("LONG" or "SHORT")
        current_stop: Current stop-loss price
        new_stop: Newly calculated stop-loss price

    Returns:
        Monotonic stop price

    Example:
        # LONG position
        stop = enforce_monotonic_stop("LONG", current_stop=98.0, new_stop=99.0)
        # Returns 99.0 (higher is better for LONG)

        stop = enforce_monotonic_stop("LONG", current_stop=99.0, new_stop=98.0)
        # Returns 99.0 (don't move stop DOWN for LONG)

        # SHORT position
        stop = enforce_monotonic_stop("SHORT", current_stop=102.0, new_stop=101.0)
        # Returns 101.0 (lower is better for SHORT)

        stop = enforce_monotonic_stop("SHORT", current_stop=101.0, new_stop=102.0)
        # Returns 101.0 (don't move stop UP for SHORT)
    """
    if direction == "LONG":
        # LONG: stop can only move UP (max)
        monotonic_stop = max(current_stop, new_stop)

        if monotonic_stop > current_stop:
            logger.info(
                f"LONG stop moved up: {current_stop:.2f} → {monotonic_stop:.2f}"
            )

    elif direction == "SHORT":
        # SHORT: stop can only move DOWN (min)
        monotonic_stop = min(current_stop, new_stop)

        if monotonic_stop < current_stop:
            logger.info(
                f"SHORT stop moved down: {current_stop:.2f} → {monotonic_stop:.2f}"
            )

    else:
        logger.warning(
            f"Unknown direction '{direction}', returning new_stop unchanged"
        )
        monotonic_stop = new_stop

    return monotonic_stop
