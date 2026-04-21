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
                    "Preview the sections that follow.",
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
                    "Highlight the essential data flow.",
                ],
                target_words=350,
            ),
            Task(
                id="s3",
                title="Worked Example",
                goal=f"Reader sees {topic} applied to a concrete, realistic scenario.",
                bullets=[
                    "Describe a realistic input or scenario.",
                    "Walk through the steps end-to-end.",
                    "Point out what the reader should notice.",
                ],
                target_words=350,
            ),
            Task(
                id="s4",
                title="Common Pitfalls",
                goal=f"Reader avoids the two most common mistakes when using {topic}.",
                bullets=[
                    "Name the first common mistake and why it happens.",
                    "Name the second common mistake and its symptom.",
                    "State a simple rule to avoid both.",
                ],
                target_words=300,
            ),
            Task(
                id="s5",
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

    fell_back = False
    if USE_MOCK:
        plan = _mock_plan(topic)
    else:
        try:
            plan = _real_plan(topic, evidence_compact)
        except Exception as e:  # noqa: BLE001
            log.warning("planner LLM failed (%s) -> falling back to mock plan", e)
            plan = _mock_plan(topic)
            fell_back = True

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    suffix = " (LLM failed, used mock)" if fell_back else ""
    return {
        "plan": plan,
        "decision_log": [
            f"{ts} planner -> {len(plan.tasks)} tasks ('{plan.blog_title}'){suffix}"
        ],
    }
