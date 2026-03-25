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
