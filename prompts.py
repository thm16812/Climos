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
