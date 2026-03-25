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
