#!/usr/bin/env python3
"""
Mirror Fish Scenario Planner
A terminal tool for testing mercy operation plans against scenarios.
"""

import sys
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

import storage
import display
from models import Scenario, MercyPlan

console = Console()


# ─── Helpers ────────────────────────────────────────────────────────────────

def _require_scenario(scenario_id: str) -> "Scenario":
    scenario = storage.load_scenario(scenario_id)
    if not scenario:
        console.print(f"[red]Scenario '{scenario_id}' not found.[/red]")
        sys.exit(1)
    return scenario


def _require_plan(scenario_id: str, plan_id: str) -> "MercyPlan":
    plan = storage.load_plan(scenario_id, plan_id)
    if not plan:
        console.print(f"[red]Plan '{plan_id}' not found.[/red]")
        sys.exit(1)
    return plan


def _prompt_list(prompt_text: str) -> list[str]:
    """Prompt for a comma-separated list, return as list of strings."""
    raw = Prompt.ask(prompt_text)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ─── CLI Root ────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Mirror Fish — Scenario Planner & Mercy Operation Effectiveness Analyzer"""
    pass


# ─── Scenario Commands ───────────────────────────────────────────────────────

@cli.group()
def scenario():
    """Manage scenarios."""
    pass


@scenario.command("new")
def scenario_new():
    """Create a new scenario interactively."""
    console.print("\n[bold cyan]Create New Scenario[/bold cyan]")
    console.print("Define the world context your mercy plans will be tested against.\n")

    name = Prompt.ask("[bold]Scenario name[/bold]")
    description = Prompt.ask("[bold]Description[/bold]")

    context_choices = ["humanitarian", "political", "environmental", "conflict", "economic", "public-health"]
    console.print(f"[bold]Context type[/bold] — options: {', '.join(context_choices)}")
    context_type = Prompt.ask("[bold]Context type[/bold]", default="humanitarian")

    console.print("\n[dim]Variables: key factors in this scenario (e.g. population=2M, conflict_level=high)[/dim]")
    vars_raw = Prompt.ask("[bold]Variables[/bold] (key=value, comma-separated, or leave blank)")
    variables = {}
    if vars_raw.strip():
        for pair in vars_raw.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, _, v = pair.partition("=")
                variables[k.strip()] = v.strip()

    console.print("\n[dim]Constraints: limiting factors (e.g. no air access, limited water)[/dim]")
    constraints = _prompt_list("[bold]Constraints[/bold] (comma-separated, or leave blank)")

    s = Scenario(
        name=name,
        description=description,
        context_type=context_type,
        variables=variables,
        constraints=constraints,
    )
    storage.save_scenario(s)
    console.print(f"\n[green]Scenario created:[/green] [bold]{s.name}[/bold] (ID: {s.id})")
    display.print_scenario(s)


@scenario.command("list")
def scenario_list():
    """List all saved scenarios."""
    scenarios = storage.list_scenarios()
    display.print_scenarios_table(scenarios)


@scenario.command("show")
@click.argument("scenario_id")
def scenario_show(scenario_id):
    """Show details of a scenario."""
    s = _require_scenario(scenario_id)
    display.print_scenario(s)

    plans = storage.list_plans(scenario_id)
    if plans:
        console.print(f"\n[dim]{len(plans)} plan(s) attached to this scenario:[/dim]")
        display.print_plans_table(plans)


@scenario.command("delete")
@click.argument("scenario_id")
def scenario_delete(scenario_id):
    """Delete a scenario."""
    s = _require_scenario(scenario_id)
    if Confirm.ask(f"Delete scenario '[bold]{s.name}[/bold]'?"):
        storage.delete_scenario(scenario_id)
        console.print("[green]Deleted.[/green]")


# ─── Plan Commands ───────────────────────────────────────────────────────────

@cli.group()
def plan():
    """Manage mercy operation plans."""
    pass


@plan.command("new")
@click.argument("scenario_id")
def plan_new(scenario_id):
    """Add a mercy operation plan to a scenario."""
    scenario = _require_scenario(scenario_id)
    console.print(f"\n[bold cyan]New Mercy Operation Plan[/bold cyan]")
    console.print(f"Scenario: [bold]{scenario.name}[/bold]\n")

    name = Prompt.ask("[bold]Plan name[/bold]")
    description = Prompt.ask("[bold]Description[/bold]")

    approach_choices = ["humanitarian", "diplomatic", "economic", "logistical", "medical", "military-humanitarian"]
    console.print(f"[bold]Approach type[/bold] — options: {', '.join(approach_choices)}")
    approach = Prompt.ask("[bold]Approach[/bold]", default="humanitarian")

    timeline_days = int(Prompt.ask("[bold]Timeline (days)[/bold]", default="30"))

    console.print("\n[dim]Resources available for this plan (e.g. 50 medics, $2M fund)[/dim]")
    resources = _prompt_list("[bold]Resources[/bold] (comma-separated)")

    console.print("\n[dim]Objectives: what this plan aims to achieve[/dim]")
    objectives = _prompt_list("[bold]Objectives[/bold] (comma-separated)")

    p = MercyPlan(
        scenario_id=scenario_id,
        name=name,
        description=description,
        approach=approach,
        resources=resources,
        timeline_days=timeline_days,
        objectives=objectives,
    )
    storage.save_plan(p)
    console.print(f"\n[green]Plan created:[/green] [bold]{p.name}[/bold] (ID: {p.id})")
    display.print_plan(p)


@plan.command("list")
@click.argument("scenario_id")
def plan_list(scenario_id):
    """List all plans for a scenario."""
    _require_scenario(scenario_id)
    plans = storage.list_plans(scenario_id)
    display.print_plans_table(plans)


@plan.command("show")
@click.argument("scenario_id")
@click.argument("plan_id")
def plan_show(scenario_id, plan_id):
    """Show details of a plan."""
    display.print_plan(_require_plan(scenario_id, plan_id))


# ─── Analyze Commands ────────────────────────────────────────────────────────

@cli.command("analyze")
@click.argument("scenario_id")
@click.option("--plan", "plan_id", default=None, help="Analyze a specific plan ID only")
@click.option("--compare", is_flag=True, help="Compare all plans side-by-side")
def analyze(scenario_id, plan_id, compare):
    """Analyze mercy plan effectiveness against a scenario."""
    import analyzer

    scenario = _require_scenario(scenario_id)

    if compare:
        plans = storage.list_plans(scenario_id)
        if len(plans) < 2:
            console.print("[red]Need at least 2 plans to compare. Use --plan or add more plans.[/red]")
            sys.exit(1)
        console.print(f"\n[bold cyan]Comparing {len(plans)} plans...[/bold cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
            p.add_task("Running comparison analysis...", total=None)
            comparison = analyzer.compare_plans(scenario, plans)
        display.print_comparison(comparison)
        return

    if plan_id:
        plans = [_require_plan(scenario_id, plan_id)]
    else:
        plans = storage.list_plans(scenario_id)
        if not plans:
            console.print("[red]No plans found. Add one with: plan new <scenario-id>[/red]")
            sys.exit(1)

    for p in plans:
        console.print(f"\n[bold]Analyzing:[/bold] {p.name}...")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as prog:
            task = prog.add_task(f"Simulating '{p.name}'...", total=None)
            report = analyzer.analyze_plan(scenario, p)
        display.print_report(report)


# ─── Report Commands ─────────────────────────────────────────────────────────

@cli.command("report")
@click.argument("scenario_id")
@click.option("--plan", "plan_id", default=None, help="Show report for a specific plan")
def report(scenario_id, plan_id):
    """View saved effectiveness reports for a scenario."""
    _require_scenario(scenario_id)

    if plan_id:
        r = storage.load_report(scenario_id, plan_id)
        if not r:
            console.print(f"[yellow]No report yet for plan {plan_id}. Run: analyze {scenario_id} --plan {plan_id}[/yellow]")
            sys.exit(1)
        display.print_report(r)
    else:
        reports = storage.list_reports(scenario_id)
        if not reports:
            console.print(f"[yellow]No reports yet. Run: analyze {scenario_id}[/yellow]")
            sys.exit(1)
        for r in reports:
            display.print_report(r)


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
