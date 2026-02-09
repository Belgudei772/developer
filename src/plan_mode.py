from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

VALID_STATUSES = {"pending", "approved", "running", "done", "failed"}


@dataclass
class PlanStep:
    id: str
    title: str
    description: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: str = ""


@dataclass
class PlanState:
    active: bool = False
    goal: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    approved_ids: set[str] = field(default_factory=set)


def _extract_json_block(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def create_plan_from_json(text: str) -> PlanState:
    raw = _extract_json_block(text)
    data = json.loads(raw)

    goal = str(data.get("goal", "")).strip()
    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list):
        raise ValueError("'steps' must be a list")

    steps: list[PlanStep] = []
    for i, item in enumerate(raw_steps, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Step {i} must be an object")
        step = PlanStep(
            id=str(item.get("id", f"step-{i}")).strip(),
            title=str(item.get("title", "")).strip(),
            description=str(item.get("description", "")).strip(),
            tool=str(item.get("tool", "")).strip(),
            args=item.get("args", {}) or {},
        )
        if not isinstance(step.args, dict):
            raise ValueError(f"Step {step.id}: 'args' must be an object")
        steps.append(step)

    return PlanState(active=True, goal=goal, steps=steps, approved_ids=set())


def validate_plan(plan: PlanState, allowed_tools: set[str]) -> None:
    if not plan.goal:
        raise ValueError("Plan goal is empty")
    if not plan.steps:
        raise ValueError("Plan has no steps")

    seen_ids: set[str] = set()
    for step in plan.steps:
        if not step.id:
            raise ValueError("A step is missing 'id'")
        if step.id in seen_ids:
            raise ValueError(f"Duplicate step id: {step.id}")
        seen_ids.add(step.id)

        if not step.title:
            raise ValueError(f"Step {step.id} is missing 'title'")
        if not step.tool:
            raise ValueError(f"Step {step.id} is missing 'tool'")
        if step.tool not in allowed_tools:
            raise ValueError(f"Step {step.id} has unsupported tool: {step.tool}")
        if step.status not in VALID_STATUSES:
            raise ValueError(f"Step {step.id} has invalid status: {step.status}")


def render_plan(plan: PlanState) -> str:
    if not plan.active:
        return "No active plan."

    lines = [f"Goal: {plan.goal}", ""]
    for step in plan.steps:
        approved = "yes" if step.id in plan.approved_ids else "no"
        lines.append(f"[{step.id}] {step.title}")
        lines.append(f"  status: {step.status} | approved: {approved}")
        lines.append(f"  tool: {step.tool} args: {step.args}")
        if step.description:
            lines.append(f"  note: {step.description}")
        if step.result:
            lines.append(f"  result: {step.result[:200]}")
        lines.append("")
    return "\n".join(lines).rstrip()


def approve_steps(plan: PlanState, target: str) -> list[str]:
    if not plan.active:
        raise ValueError("No active plan to approve")

    approved: list[str] = []
    if target == "all":
        for step in plan.steps:
            if step.status in {"pending", "approved"}:
                plan.approved_ids.add(step.id)
                if step.status == "pending":
                    step.status = "approved"
                approved.append(step.id)
        return approved

    for step in plan.steps:
        if step.id == target:
            plan.approved_ids.add(step.id)
            if step.status == "pending":
                step.status = "approved"
            approved.append(step.id)
            return approved

    raise ValueError(f"Unknown step id: {target}")


def get_runnable_steps(plan: PlanState) -> list[PlanStep]:
    if not plan.active:
        return []
    return [
        step
        for step in plan.steps
        if step.id in plan.approved_ids and step.status in {"approved", "pending"}
    ]


def mark_step_result(plan: PlanState, step_id: str, ok: bool, result: str) -> None:
    for step in plan.steps:
        if step.id == step_id:
            step.status = "done" if ok else "failed"
            step.result = result
            return
    raise ValueError(f"Unknown step id: {step_id}")


def reset_plan() -> PlanState:
    return PlanState(active=False, goal="", steps=[], approved_ids=set())
