"""Router node - classifies topic via Groq JSON mode."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from blog_agent.llm import get_llm
from blog_agent.logger import get_logger
from blog_agent.prompts.router import ROUTER_SYSTEM, ROUTER_USER_TEMPLATE
from blog_agent.schemas import AgentState, RouterDecision

log = get_logger("router")

USE_MOCK = os.environ.get("BLOG_AGENT_ROUTER_MOCK", "0") == "1"


def _mock_decision() -> RouterDecision:
    return RouterDecision(
        needs_research=False,
        mode="closed_book",
        queries=[],
        reasoning="mock router - closed book default",
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _real_decision(topic: str) -> RouterDecision:
    llm = get_llm(temperature=0.1).with_structured_output(RouterDecision)
    messages = [
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=ROUTER_USER_TEMPLATE.format(topic=topic)),
    ]
    result = llm.invoke(messages)
    assert isinstance(result, RouterDecision), "Malformed LLM output"
    # Safety: keep the mode/needs_research/queries fields consistent regardless
    # of what the LLM returned.
    if result.mode == "closed_book":
        result = result.model_copy(update={"needs_research": False, "queries": []})
    else:  # open_book or hybrid
        result = result.model_copy(update={"needs_research": True})
    return result


def router_node(state: AgentState) -> dict:
    topic = state["topic"]
    log.info("router: topic=%r mock=%s", topic, USE_MOCK)

    decision = _mock_decision() if USE_MOCK else _real_decision(topic)

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "router_decision": decision,
        "decision_log": [
            f"{ts} router -> mode={decision.mode} research={decision.needs_research} "
            f"queries={len(decision.queries)}"
        ],
    }
