"""CLI Tool for JSON Strategy Configuration Management.

Provides commands for:
- Validating JSON configs
- Converting hardcoded strategies to JSON
- Listing available strategies
- Comparing JSON vs hardcoded strategies
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from ..migration.json_generator import JSONConfigGenerator
from ..migration.strategy_analyzer import StrategyAnalyzer
from ..strategy_catalog import StrategyCatalog
from .loader import ConfigLoader

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="tradingbot-config")
def cli():
    """TradingBot JSON Configuration CLI Tool.

    Manage JSON strategy configurations, validate configs, and convert
    hardcoded strategies to JSON format.
    """
    pass


@cli.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation output")
def validate(config_path: str, verbose: bool):
    """Validate a JSON configuration file.

    Performs two-stage validation:
    1. JSON Schema validation (structure & types)
    2. Pydantic model validation (business logic)

    Examples:
        tradingbot-config validate configs/production.json
        tradingbot-config validate configs/strategy.json --verbose
    """
    try:
        loader = ConfigLoader()
        config = loader.load_config(Path(config_path))

        console.print("[green]✓ Configuration valid![/green]")
        console.print(f"  Schema version: {config.schema_version}")
        console.print(f"  Indicators: {len(config.indicators)}")
        console.print(f"  Regimes: {len(config.regimes)}")
        console.print(f"  Strategies: {len(config.strategies)}")
        console.print(f"  Strategy Sets: {len(config.strategy_sets)}")
        console.print(f"  Routing Rules: {len(config.routing)}")

        if verbose:
            console.print("\n[bold]Indicators:[/bold]")
            for ind in config.indicators:
                console.print(f"  • {ind.id} ({ind.type})")

            console.print("\n[bold]Regimes:[/bold]")
            for regime in config.regimes:
                console.print(f"  • {regime.id}: {regime.name} (priority={regime.priority})")

            console.print("\n[bold]Strategies:[/bold]")
            for strategy in config.strategies:
                console.print(f"  • {strategy.id}: {strategy.name}")

    except Exception as e:
        console.print(f"[red]✗ Validation failed:[/red] {e}", style="bold")
        sys.exit(1)


@cli.command()
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table",
              help="Output format")
def list_strategies(format: str):
    """List all available hardcoded strategies.

    Shows strategy names, types, applicable regimes, and descriptions.

    Examples:
        tradingbot-config list-strategies
        tradingbot-config list-strategies --format json
    """
    catalog = StrategyCatalog()
    strategies = catalog.get_all_strategies()

    if format == "json":
        data = [
            {
                "name": s.profile.name,
                "type": s.strategy_type.value,
                "description": s.profile.description,
                "regimes": [r.value for r in s.profile.regimes],
                "entry_rules": len(s.entry_rules),
                "exit_rules": len(s.exit_rules),
            }
            for s in strategies
        ]
        console.print_json(json.dumps(data, indent=2))
    else:
        table = Table(title="Available Hardcoded Strategies", show_lines=True)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Regimes", style="yellow")
        table.add_column("Description", style="white")

        for s in strategies:
            table.add_row(
                s.profile.name,
                s.strategy_type.value,
                ", ".join(r.value for r in s.profile.regimes),
                s.profile.description[:60] + "..." if len(s.profile.description) > 60 else s.profile.description,
            )

        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(strategies)} strategies")


@cli.command()
@click.argument("strategy_name")
@click.option("--output", "-o", required=True, type=click.Path(),
              help="Output JSON file path")
@click.option("--include-regime/--no-regime", default=True,
              help="Auto-generate regime from strategy conditions")
@click.option("--include-set/--no-set", default=True,
              help="Generate strategy set and routing")
@click.option("--pretty/--compact", default=True,
              help="Pretty-print JSON output")
def convert(strategy_name: str, output: str, include_regime: bool, include_set: bool, pretty: bool):
    """Convert a hardcoded strategy to JSON configuration.

    Analyzes the strategy's entry/exit rules and generates equivalent
    JSON configuration.

    Examples:
        tradingbot-config convert trend_following_conservative -o configs/trend.json
        tradingbot-config convert mean_reversion_bb -o configs/mean_rev.json --no-regime
    """
    try:
        # Load strategy from catalog
        catalog = StrategyCatalog()
        strategy_def = catalog.get_strategy(strategy_name)

        if strategy_def is None:
            console.print(f"[red]✗ Strategy '{strategy_name}' not found![/red]")
            console.print("\nAvailable strategies:")
            for s in catalog.get_all_strategies():
                console.print(f"  • {s.profile.name}")
            sys.exit(1)

        # Analyze strategy
        console.print(f"[cyan]Analyzing strategy:[/cyan] {strategy_name}")
        analyzer = StrategyAnalyzer()
        analysis = analyzer.analyze_strategy_definition(strategy_def)

        console.print(f"  Entry conditions: {len(analysis.entry_conditions)}")
        console.print(f"  Exit conditions: {len(analysis.exit_conditions)}")
        console.print(f"  Required indicators: {len(analysis.required_indicators)}")
        console.print(f"  Strategy type: {analysis.strategy_type}")

        # Generate JSON config
        console.print("\n[cyan]Generating JSON configuration...[/cyan]")
        generator = JSONConfigGenerator()
        config = generator.generate_from_analysis(
            analysis,
            include_regime=include_regime,
            include_strategy_set=include_set
        )

        # Save to file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        indent = 2 if pretty else None
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=indent, ensure_ascii=False)
            if pretty:
                f.write("\n")

        console.print(f"[green]✓ Configuration saved to:[/green] {output_path}")

        # Show summary
        console.print("\n[bold]Generated config contains:[/bold]")
        console.print(f"  Indicators: {len(config['indicators'])}")
        console.print(f"  Regimes: {len(config['regimes'])}")
        console.print(f"  Strategies: {len(config['strategies'])}")
        console.print(f"  Strategy Sets: {len(config['strategy_sets'])}")
        console.print(f"  Routing Rules: {len(config['routing'])}")

        console.print("\n[yellow]Next steps:[/yellow]")
        console.print(f"  1. Validate: tradingbot-config validate {output}")
        console.print("  2. Test in paper trading")
        console.print("  3. Review and adjust parameters")

    except Exception as e:
        console.print(f"[red]✗ Conversion failed:[/red] {e}", style="bold")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("strategy_names", nargs=-1, required=True)
@click.option("--output", "-o", required=True, type=click.Path(),
              help="Output JSON file path")
@click.option("--pretty/--compact", default=True,
              help="Pretty-print JSON output")
def convert_multiple(strategy_names: tuple[str, ...], output: str, pretty: bool):
    """Convert multiple hardcoded strategies to a single JSON config.

    Combines multiple strategies into one configuration file with
    shared indicators and separate strategy sets for each strategy type.

    Examples:
        tradingbot-config convert-multiple trend_following_conservative mean_reversion_bb -o configs/multi.json
        tradingbot-config convert-multiple trend_* -o configs/all_trends.json
    """
    try:
        catalog = StrategyCatalog()
        all_strategies = {s.profile.name: s for s in catalog.get_all_strategies()}

        # Resolve wildcards and validate names
        resolved_names = set()
        for pattern in strategy_names:
            if "*" in pattern:
                # Wildcard matching
                prefix = pattern.rstrip("*")
                matches = [name for name in all_strategies.keys() if name.startswith(prefix)]
                resolved_names.update(matches)
            else:
                if pattern not in all_strategies:
                    console.print(f"[red]✗ Strategy '{pattern}' not found![/red]")
                    sys.exit(1)
                resolved_names.add(pattern)

        if not resolved_names:
            console.print("[red]✗ No strategies matched![/red]")
            sys.exit(1)

        console.print(f"[cyan]Converting {len(resolved_names)} strategies:[/cyan]")
        for name in sorted(resolved_names):
            console.print(f"  • {name}")

        # Analyze all strategies
        analyzer = StrategyAnalyzer()
        analyses = []
        for name in resolved_names:
            strategy_def = all_strategies[name]
            analysis = analyzer.analyze_strategy_definition(strategy_def)
            analyses.append(analysis)

        # Generate combined config
        console.print("\n[cyan]Generating combined JSON configuration...[/cyan]")
        generator = JSONConfigGenerator()
        config = generator.generate_from_multiple_analyses(analyses)

        # Save to file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        indent = 2 if pretty else None
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=indent, ensure_ascii=False)
            if pretty:
                f.write("\n")

        console.print(f"[green]✓ Combined configuration saved to:[/green] {output_path}")

        # Show summary
        console.print("\n[bold]Generated config contains:[/bold]")
        console.print(f"  Indicators: {len(config['indicators'])}")
        console.print(f"  Regimes: {len(config['regimes'])}")
        console.print(f"  Strategies: {len(config['strategies'])}")
        console.print(f"  Strategy Sets: {len(config['strategy_sets'])}")
        console.print(f"  Routing Rules: {len(config['routing'])}")

    except Exception as e:
        console.print(f"[red]✗ Conversion failed:[/red] {e}", style="bold")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.argument("strategy_name")
@click.option("--strategy-id", help="Strategy ID in JSON config (defaults to strategy_name)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed comparison output")
def compare(config_path: str, strategy_name: str, strategy_id: str | None, verbose: bool):
    """Compare JSON config against hardcoded strategy.

    Shows differences between the JSON configuration and the original
    hardcoded strategy definition.

    Examples:
        tradingbot-config compare configs/trend.json trend_following_conservative
        tradingbot-config compare configs/custom.json trend_following_conservative --strategy-id custom_trend
    """
    try:
        from ..migration.strategy_comparator import StrategyComparator

        # Load JSON config
        loader = ConfigLoader()
        json_config = loader.load_config(Path(config_path))

        # Default strategy ID to strategy name if not provided
        if strategy_id is None:
            strategy_id = strategy_name

        # Perform comparison
        console.print(f"[cyan]Comparing JSON config vs hardcoded strategy...[/cyan]")
        console.print(f"  JSON config: {config_path}")
        console.print(f"  Strategy ID: {strategy_id}")
        console.print(f"  Hardcoded: {strategy_name}")
        console.print()

        comparator = StrategyComparator()
        result = comparator.compare_json_to_hardcoded(
            json_config=json_config,
            strategy_id=strategy_id,
            hardcoded_strategy_name=strategy_name,
        )

        # Display results
        _display_comparison_result(result, verbose)

        # Exit code: 0 if equivalent, 1 if different
        sys.exit(0 if result.is_equivalent else 1)

    except Exception as e:
        console.print(f"[red]✗ Comparison failed:[/red] {e}", style="bold")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


def _display_comparison_result(result: Any, verbose: bool) -> None:
    """Display comparison result with rich formatting.

    Args:
        result: ComparisonResult object
        verbose: Show detailed output
    """
    from rich.panel import Panel
    from rich.table import Table

    # Header
    if result.is_equivalent:
        console.print(
            Panel(
                f"[green]✓ Strategies are EQUIVALENT[/green]\n"
                f"Similarity: {result.overall_similarity:.1%}",
                title=f"Comparison: {result.strategy_name}",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]✗ Strategies DIFFER[/red]\n"
                f"Similarity: {result.overall_similarity:.1%}",
                title=f"Comparison: {result.strategy_name}",
                border_style="red",
            )
        )

    # Summary table
    summary_table = Table(title="Component Comparison", show_lines=False)
    summary_table.add_column("Component", style="cyan")
    summary_table.add_column("Status", style="white")

    def _status_icon(matches: bool) -> str:
        return "[green]✓ Match[/green]" if matches else "[red]✗ Differ[/red]"

    summary_table.add_row("Entry Conditions", _status_icon(result.entry_conditions_match))
    summary_table.add_row("Exit Conditions", _status_icon(result.exit_conditions_match))
    summary_table.add_row("Risk Parameters", _status_icon(result.risk_parameters_match))
    summary_table.add_row("Indicators", _status_icon(result.indicators_match))
    summary_table.add_row("Regimes", _status_icon(result.regimes_match))

    console.print(summary_table)

    # Detailed differences (if verbose or if there are differences)
    if verbose or not result.is_equivalent:
        # Condition differences
        if result.condition_diffs:
            console.print("\n[bold]Condition Differences:[/bold]")
            cond_table = Table(show_lines=True)
            cond_table.add_column("Field", style="yellow")
            cond_table.add_column("Index", style="cyan")
            cond_table.add_column("JSON", style="green")
            cond_table.add_column("Hardcoded", style="blue")
            cond_table.add_column("Type", style="magenta")
            cond_table.add_column("Severity", style="red")

            for diff in result.condition_diffs:
                cond_table.add_row(
                    diff.field,
                    str(diff.index),
                    diff.json_condition,
                    diff.hardcoded_condition,
                    diff.difference_type,
                    diff.severity,
                )

            console.print(cond_table)

        # Risk parameter differences
        if result.parameter_diffs:
            console.print("\n[bold]Risk Parameter Differences:[/bold]")
            param_table = Table(show_lines=False)
            param_table.add_column("Parameter", style="yellow")
            param_table.add_column("JSON Value", style="green")
            param_table.add_column("Hardcoded Value", style="blue")
            param_table.add_column("Difference", style="red")

            for diff in result.parameter_diffs:
                diff_str = (
                    f"{diff.difference_pct:.1f}%"
                    if diff.difference_pct is not None
                    else "N/A"
                )
                param_table.add_row(
                    diff.parameter_name,
                    str(diff.json_value),
                    str(diff.hardcoded_value),
                    diff_str,
                )

            console.print(param_table)

        # Indicator differences
        if result.missing_indicators or result.extra_indicators:
            console.print("\n[bold]Indicator Differences:[/bold]")
            if result.missing_indicators:
                console.print(
                    f"  [red]Missing in JSON:[/red] {', '.join(result.missing_indicators)}"
                )
            if result.extra_indicators:
                console.print(
                    f"  [yellow]Extra in JSON:[/yellow] {', '.join(result.extra_indicators)}"
                )

        # Regime differences
        if result.regime_diffs:
            console.print("\n[bold]Regime Differences:[/bold]")
            for diff in result.regime_diffs:
                console.print(f"  • {diff}")

    # Warnings
    if result.warnings:
        console.print("\n[bold red]Warnings:[/bold red]")
        for warning in result.warnings:
            console.print(f"  ⚠ {warning}")

    # Notes
    if result.notes:
        console.print("\n[bold]Notes:[/bold]")
        for note in result.notes:
            console.print(f"  • {note}")

    # Recommendations
    console.print("\n[bold yellow]Recommendations:[/bold yellow]")
    if result.is_equivalent:
        console.print("  ✓ JSON config is equivalent to hardcoded strategy")
        console.print("  ✓ Safe to deploy to production")
    elif result.overall_similarity > 0.90:
        console.print("  → Review minor differences before deployment")
        console.print("  → Consider adjusting JSON config to match hardcoded exactly")
    elif result.overall_similarity > 0.75:
        console.print("  ⚠ Moderate differences detected")
        console.print("  ⚠ Carefully test in paper trading before production")
    else:
        console.print("  ✗ Significant differences detected")
        console.print("  ✗ Do NOT deploy without thorough testing")
        console.print("  ✗ Consider regenerating JSON config")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--recursive", "-r", is_flag=True, help="Search recursively")
def list_configs(directory: str, recursive: bool):
    """List all JSON config files in a directory.

    Examples:
        tradingbot-config list-configs 03_JSON/Trading_Bot/configs
        tradingbot-config list-configs configs/ --recursive
    """
    dir_path = Path(directory)
    pattern = "**/*.json" if recursive else "*.json"
    config_files = list(dir_path.glob(pattern))

    if not config_files:
        console.print(f"[yellow]No JSON files found in {directory}[/yellow]")
        return

    table = Table(title=f"JSON Config Files in {directory}", show_lines=False)
    table.add_column("File", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Valid", style="yellow")

    loader = ConfigLoader()
    for config_file in sorted(config_files):
        size = config_file.stat().st_size
        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"

        # Try to validate
        try:
            loader.load_config(config_file)
            valid = "✓"
        except Exception:
            valid = "✗"

        table.add_row(str(config_file.relative_to(dir_path)), size_str, valid)

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(config_files)} config files")


if __name__ == "__main__":
    cli()
