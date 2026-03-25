from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from models import Scenario, MercyPlan, EffectivenessReport

console = Console()


def _score_color(score: float) -> str:
    if score >= 7.5:
        return "bold green"
    elif score >= 5.0:
        return "bold yellow"
    elif score >= 3.0:
        return "bold orange1"
    return "bold red"


def print_scenario(scenario: Scenario) -> None:
    lines = [
        f"[bold]ID:[/bold] {scenario.id}",
        f"[bold]Type:[/bold] {scenario.context_type}",
        f"[bold]Description:[/bold] {scenario.description}",
    ]
    if scenario.variables:
        vars_str = ", ".join(f"{k}={v}" for k, v in scenario.variables.items())
        lines.append(f"[bold]Variables:[/bold] {vars_str}")
    if scenario.constraints:
        lines.append(f"[bold]Constraints:[/bold]")
        for c in scenario.constraints:
            lines.append(f"  • {c}")
    console.print(Panel("\n".join(lines), title=f"[cyan]{scenario.name}[/cyan]", expand=False))


def print_plan(plan: MercyPlan) -> None:
    lines = [
        f"[bold]ID:[/bold] {plan.id}",
        f"[bold]Approach:[/bold] {plan.approach}",
        f"[bold]Timeline:[/bold] {plan.timeline_days} days",
        f"[bold]Description:[/bold] {plan.description}",
    ]
    if plan.resources:
        lines.append("[bold]Resources:[/bold]")
        for r in plan.resources:
            lines.append(f"  • {r}")
    if plan.objectives:
        lines.append("[bold]Objectives:[/bold]")
        for o in plan.objectives:
            lines.append(f"  • {o}")
    console.print(Panel("\n".join(lines), title=f"[cyan]{plan.name}[/cyan]", expand=False))


def print_report(report: EffectivenessReport) -> None:
    score_style = _score_color(report.effectiveness_score)
    score_text = Text(f"{report.effectiveness_score:.1f} / 10.0", style=score_style)

    header_lines = [
        f"[bold]Plan:[/bold] {report.plan_name}",
        f"[bold]Effectiveness:[/bold] ",
        f"[bold]Confidence:[/bold] {report.confidence.upper()}",
        f"[bold]Generated:[/bold] {report.generated_at[:19].replace('T', ' ')}",
    ]

    console.print()
    console.print(Panel(
        "\n".join(header_lines),
        title="[bold cyan]EFFECTIVENESS REPORT[/bold cyan]",
        expand=False
    ))
    console.print(f"  Effectiveness Score: ", end="")
    console.print(score_text)

    # Predicted outcomes
    outcomes_table = Table(box=box.SIMPLE, show_header=False, expand=False)
    outcomes_table.add_column("", style="green")
    for o in report.predicted_outcomes:
        outcomes_table.add_row(f"✓ {o}")
    console.print(Panel(outcomes_table, title="[green]Predicted Outcomes[/green]", expand=False))

    # Risks
    risks_table = Table(box=box.SIMPLE, show_header=False, expand=False)
    risks_table.add_column("", style="red")
    for r in report.risks:
        risks_table.add_row(f"⚠ {r}")
    console.print(Panel(risks_table, title="[red]Risks[/red]", expand=False))

    # Recommendations
    rec_table = Table(box=box.SIMPLE, show_header=False, expand=False)
    rec_table.add_column("", style="blue")
    for i, r in enumerate(report.recommendations, 1):
        rec_table.add_row(f"{i}. {r}")
    console.print(Panel(rec_table, title="[blue]Recommendations[/blue]", expand=False))

    # Narrative
    console.print(Panel(
        report.simulation_narrative,
        title="[magenta]Simulation Narrative[/magenta]",
        expand=False
    ))


def print_comparison(comparison: list[dict]) -> None:
    table = Table(title="Plan Comparison", box=box.ROUNDED)
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Plan", style="cyan")
    table.add_column("Score", justify="center")
    table.add_column("Key Advantage", style="green")
    table.add_column("Key Weakness", style="red")

    for item in comparison:
        score = item.get("effectiveness_score", 0)
        score_style = _score_color(score)
        table.add_row(
            f"#{item['rank']}",
            item["plan_name"],
            Text(f"{score:.1f}", style=score_style),
            item.get("key_advantage", ""),
            item.get("key_weakness", ""),
        )
    console.print(table)


def print_scenarios_table(scenarios: list[Scenario]) -> None:
    if not scenarios:
        console.print("[yellow]No scenarios found. Create one with: scenario new[/yellow]")
        return
    table = Table(title="Saved Scenarios", box=box.ROUNDED)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Created")
    for s in scenarios:
        table.add_row(s.id, s.name, s.context_type, s.created_at[:10])
    console.print(table)


def print_plans_table(plans: list[MercyPlan]) -> None:
    if not plans:
        console.print("[yellow]No plans found. Create one with: plan new <scenario-id>[/yellow]")
        return
    table = Table(title="Mercy Operation Plans", box=box.ROUNDED)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Approach")
    table.add_column("Timeline")
    table.add_column("Created")
    for p in plans:
        table.add_row(p.id, p.name, p.approach, f"{p.timeline_days}d", p.created_at[:10])
    console.print(table)
