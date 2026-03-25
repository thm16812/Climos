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
