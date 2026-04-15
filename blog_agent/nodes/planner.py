"""Planner node - produces a structured Plan via Groq JSON mode."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from blog_agent.llm import get_llm
from blog_agent.logger import get_logger
from blog_agent.prompts.planner import (
    PLANNER_SYSTEM,
    PLANNER_USER_TEMPLATE,
    format_evidence_block,
)
from blog_agent.schemas import AgentState, Plan, Task

log = get_logger("planner")

# Tests flip this to True via monkeypatch to avoid network calls.
USE_MOCK = os.environ.get("BLOG_AGENT_PLANNER_MOCK", "0") == "1"


def _mock_plan(topic: str) -> Plan:
    return Plan(
        blog_title=f"A Short Guide to {topic}",
        audience="technically curious readers",
        tone="clear, didactic",
        kind="explainer",
        constraints=[],
        tasks=[
            Task(
                id="s1",
                title="Introduction",
                goal=f"Reader understands why {topic} matters and what the post will cover.",
                bullets=[
                    f"Define {topic} in one sentence.",
                    "Name two concrete use cases.",
                    "Preview the three sections that follow.",
                ],
                target_words=180,
            ),
            Task(
                id="s2",
                title="Core Mechanics",
                goal=f"Reader grasps how {topic} works at a mechanical level.",
                bullets=[
                    "Identify the main components.",
                    "Describe how components interact.",
                    "Highlight one common pitfall.",
                ],
                target_words=350,
            ),
            Task(
                id="s3",
                title="Conclusion",
                goal="Reader walks away with a 3-line summary and one action to try.",
                bullets=[
                    "Summarize the core mechanic.",
                    "Call out the main use case.",
                    "Suggest one next step for the reader.",
                ],
                target_words=160,
            ),
        ],
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _real_plan(topic: str, evidence_compact: str) -> Plan:
    llm = get_llm(temperature=0.3).with_structured_output(Plan)
    messages = [
        SystemMessage(content=PLANNER_SYSTEM),
        HumanMessage(
            content=PLANNER_USER_TEMPLATE.format(
                topic=topic,
                evidence_block=format_evidence_block(evidence_compact),
            )
        ),
    ]
    result = llm.invoke(messages)
    assert isinstance(result, Plan), "Malformed LLM output"
    return result


def planner_node(state: AgentState) -> dict:
    topic = state["topic"]
    evidence = state.get("evidence_pack")
    evidence_compact = evidence.compact_context() if evidence else ""
    log.info("planner: topic=%r evidence=%d", topic, len(evidence.items) if evidence else 0)

    plan = _mock_plan(topic) if USE_MOCK else _real_plan(topic, evidence_compact)

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "plan": plan,
        "decision_log": [f"{ts} planner -> {len(plan.tasks)} tasks ('{plan.blog_title}')"],
    }
