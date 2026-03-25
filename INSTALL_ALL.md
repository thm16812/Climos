# Mirror Fish — Complete Setup & Copy-Paste File

Copy each section below into the corresponding file in a new folder on your MacBook.

---

## STEP 1 — Create your project folder

Open Terminal and run:
```bash
mkdir ~/mirror-fish
cd ~/mirror-fish
```

---

## STEP 2 — Create each file

### `requirements.txt`
```
anthropic>=0.40.0
click>=8.1.0
rich>=13.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

### `.env.example`
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MODEL=claude-sonnet-4-6
MAX_TOKENS=2000
```

---

### `config.py`
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

STORAGE_DIR = Path(os.getenv("CLIMOS_DATA_DIR", Path.home() / ".climos"))


def validate_config() -> None:
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
```

---

### `models.py`
```python
from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
import uuid


def new_id() -> str:
    return uuid.uuid4().hex[:8]


class Scenario(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    description: str
    context_type: str  # humanitarian, political, environmental, conflict, economic
    variables: dict[str, str] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class MercyPlan(BaseModel):
    id: str = Field(default_factory=new_id)
    scenario_id: str
    name: str
    description: str
    approach: str  # humanitarian, diplomatic, economic, logistical, medical
    resources: list[str] = Field(default_factory=list)
    timeline_days: int
    objectives: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class EffectivenessReport(BaseModel):
    scenario_id: str
    plan_id: str
    plan_name: str
    effectiveness_score: float  # 0.0 – 10.0
    confidence: Literal["low", "medium", "high"]
    predicted_outcomes: list[str]
    risks: list[str]
    recommendations: list[str]
    simulation_narrative: str
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
```

---

### `storage.py`
```python
import json
from pathlib import Path
from typing import Optional

from config import STORAGE_DIR
from models import Scenario, MercyPlan, EffectivenessReport


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _scenarios_dir() -> Path:
    return _ensure(STORAGE_DIR / "scenarios")


def _plans_dir(scenario_id: str) -> Path:
    return _ensure(STORAGE_DIR / "plans" / scenario_id)


def _reports_dir(scenario_id: str) -> Path:
    return _ensure(STORAGE_DIR / "reports" / scenario_id)


# --- Scenarios ---

def save_scenario(scenario: Scenario) -> None:
    path = _scenarios_dir() / f"{scenario.id}.json"
    path.write_text(scenario.model_dump_json(indent=2))


def load_scenario(scenario_id: str) -> Optional[Scenario]:
    path = _scenarios_dir() / f"{scenario_id}.json"
    if not path.exists():
        return None
    return Scenario.model_validate_json(path.read_text())


def list_scenarios() -> list[Scenario]:
    return [
        Scenario.model_validate_json(p.read_text())
        for p in sorted(_scenarios_dir().glob("*.json"))
    ]


def delete_scenario(scenario_id: str) -> bool:
    path = _scenarios_dir() / f"{scenario_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


# --- Plans ---

def save_plan(plan: MercyPlan) -> None:
    path = _plans_dir(plan.scenario_id) / f"{plan.id}.json"
    path.write_text(plan.model_dump_json(indent=2))


def load_plan(scenario_id: str, plan_id: str) -> Optional[MercyPlan]:
    path = _plans_dir(scenario_id) / f"{plan_id}.json"
    if not path.exists():
        return None
    return MercyPlan.model_validate_json(path.read_text())


def list_plans(scenario_id: str) -> list[MercyPlan]:
    return [
        MercyPlan.model_validate_json(p.read_text())
        for p in sorted(_plans_dir(scenario_id).glob("*.json"))
    ]


# --- Reports ---

def save_report(report: EffectivenessReport) -> None:
    path = _reports_dir(report.scenario_id) / f"{report.plan_id}.json"
    path.write_text(report.model_dump_json(indent=2))


def load_report(scenario_id: str, plan_id: str) -> Optional[EffectivenessReport]:
    path = _reports_dir(scenario_id) / f"{plan_id}.json"
    if not path.exists():
        return None
    return EffectivenessReport.model_validate_json(path.read_text())


def list_reports(scenario_id: str) -> list[EffectivenessReport]:
    return [
        EffectivenessReport.model_validate_json(p.read_text())
        for p in sorted(_reports_dir(scenario_id).glob("*.json"))
    ]
```

---

### `prompts.py`
```python
import json
from models import Scenario, MercyPlan

SYSTEM_PROMPT = """You are a strategic simulation analyst specializing in humanitarian operations,
conflict resolution, and mercy-based interventions. You assess operation plans against real-world
scenarios using evidence-based reasoning and historical precedent.

Your analysis must be:
- Grounded in the specific variables and constraints of the scenario
- Honest about limitations and risks
- Actionable in recommendations
- Written for decision-makers who need clarity, not jargon

Always return valid JSON only — no markdown fences, no preamble."""


def build_analysis_prompt(scenario: Scenario, plan: MercyPlan) -> str:
    scenario_data = {
        "name": scenario.name,
        "description": scenario.description,
        "context_type": scenario.context_type,
        "variables": scenario.variables,
        "constraints": scenario.constraints,
    }
    plan_data = {
        "name": plan.name,
        "description": plan.description,
        "approach": plan.approach,
        "resources": plan.resources,
        "timeline_days": plan.timeline_days,
        "objectives": plan.objectives,
    }

    return f"""Analyze this mercy operation plan against the given scenario and return a JSON object.

SCENARIO:
{json.dumps(scenario_data, indent=2)}

MERCY OPERATION PLAN:
{json.dumps(plan_data, indent=2)}

Return a JSON object with exactly these fields:
{{
  "effectiveness_score": <float 0.0-10.0>,
  "confidence": "<low|medium|high>",
  "predicted_outcomes": ["<outcome 1>", "<outcome 2>", ...],
  "risks": ["<risk 1>", "<risk 2>", ...],
  "recommendations": ["<recommendation 1>", "<recommendation 2>", ...],
  "simulation_narrative": "<2-3 paragraph narrative of how the plan plays out in this scenario>"
}}

Rules:
- effectiveness_score: 0 = completely ineffective, 10 = maximally effective
- predicted_outcomes: 3-5 specific, measurable outcomes
- risks: 3-5 concrete risks or failure modes
- recommendations: 3-5 actionable improvements to the plan
- simulation_narrative: describe the plan's execution step by step, including friction points and likely results"""


def build_comparison_prompt(scenario: Scenario, plans: list[MercyPlan]) -> str:
    scenario_data = {
        "name": scenario.name,
        "description": scenario.description,
        "context_type": scenario.context_type,
        "variables": scenario.variables,
        "constraints": scenario.constraints,
    }
    plans_data = [
        {
            "id": p.id,
            "name": p.name,
            "approach": p.approach,
            "timeline_days": p.timeline_days,
            "resources": p.resources,
        }
        for p in plans
    ]

    return f"""Compare these mercy operation plans for the given scenario and rank them by effectiveness.

SCENARIO:
{json.dumps(scenario_data, indent=2)}

PLANS TO COMPARE:
{json.dumps(plans_data, indent=2)}

Return a JSON array, each item:
{{
  "plan_id": "<id>",
  "plan_name": "<name>",
  "rank": <1 = best>,
  "effectiveness_score": <float 0.0-10.0>,
  "key_advantage": "<one sentence>",
  "key_weakness": "<one sentence>"
}}"""
```

---

### `analyzer.py`
```python
import json
from typing import Optional

import anthropic

from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, validate_config
from models import Scenario, MercyPlan, EffectivenessReport
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_comparison_prompt
import storage


def _client() -> anthropic.Anthropic:
    validate_config()
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_plan(scenario: Scenario, plan: MercyPlan) -> EffectivenessReport:
    """Run Claude analysis for a single mercy plan against a scenario."""
    client = _client()
    prompt = build_analysis_prompt(scenario, plan)

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\n\nRaw response:\n{raw}")

    report = EffectivenessReport(
        scenario_id=scenario.id,
        plan_id=plan.id,
        plan_name=plan.name,
        effectiveness_score=float(data["effectiveness_score"]),
        confidence=data["confidence"],
        predicted_outcomes=data["predicted_outcomes"],
        risks=data["risks"],
        recommendations=data["recommendations"],
        simulation_narrative=data["simulation_narrative"],
    )
    storage.save_report(report)
    return report


def compare_plans(scenario: Scenario, plans: list[MercyPlan]) -> list[dict]:
    """Compare multiple mercy plans and return a ranked list."""
    if len(plans) < 2:
        raise ValueError("Need at least 2 plans to compare.")

    client = _client()
    prompt = build_comparison_prompt(scenario, plans)

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\n\nRaw response:\n{raw}")

    return sorted(data, key=lambda x: x.get("rank", 99))
```

---

### `display.py`
```python
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

    outcomes_table = Table(box=box.SIMPLE, show_header=False, expand=False)
    outcomes_table.add_column("", style="green")
    for o in report.predicted_outcomes:
        outcomes_table.add_row(f"✓ {o}")
    console.print(Panel(outcomes_table, title="[green]Predicted Outcomes[/green]", expand=False))

    risks_table = Table(box=box.SIMPLE, show_header=False, expand=False)
    risks_table.add_column("", style="red")
    for r in report.risks:
        risks_table.add_row(f"⚠ {r}")
    console.print(Panel(risks_table, title="[red]Risks[/red]", expand=False))

    rec_table = Table(box=box.SIMPLE, show_header=False, expand=False)
    rec_table.add_column("", style="blue")
    for i, r in enumerate(report.recommendations, 1):
        rec_table.add_row(f"{i}. {r}")
    console.print(Panel(rec_table, title="[blue]Recommendations[/blue]", expand=False))

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
```

---

### `main.py`
```python
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
            console.print("[red]Need at least 2 plans to compare.[/red]")
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
```

---

## STEP 3 — Install & configure

```bash
cd ~/mirror-fish
pip install -r requirements.txt
cp .env.example .env
# Edit .env and paste your Anthropic API key
```

Get your API key at: https://console.anthropic.com/

---

## STEP 4 — Run it

```bash
# See all commands
python main.py --help

# Create your first scenario
python main.py scenario new

# Add a mercy operation plan
python main.py plan new <scenario-id>

# Analyze effectiveness
python main.py analyze <scenario-id>

# Compare multiple plans
python main.py analyze <scenario-id> --compare

# View saved reports
python main.py report <scenario-id>
```

---

## STEP 5 — Open with Claude Code

```bash
cd ~/mirror-fish
claude  # opens Claude Code in this folder
```

Claude Code will automatically read `CLAUDE.md` to understand the project.
(Also create a `CLAUDE.md` file — contents are in the repo.)
