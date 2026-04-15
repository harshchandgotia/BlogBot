"""LangGraph assembly + top-level `run(topic)` entry point.

No business logic lives here - just wiring.
"""
from __future__ import annotations

from typing import Any

from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Send

from blog_agent.logger import get_logger
from blog_agent.nodes.planner import planner_node
from blog_agent.nodes.reducer.image_gen import image_gen_node
from blog_agent.nodes.reducer.image_plan import image_plan_node
from blog_agent.nodes.reducer.merge import merge_node
from blog_agent.nodes.research import research_node
from blog_agent.nodes.router import router_node
from blog_agent.nodes.worker import worker_node
from blog_agent.schemas import AgentState

log = get_logger("graph")


def _route_after_router(state: AgentState) -> str:
    decision = state["router_decision"]
    if decision is not None and decision.needs_research:
        return "research_node"
    return "planner_node"


def _fan_out(state: AgentState) -> list[Send]:
    plan = state["plan"]
    assert plan is not None, "fan_out requires a plan"
    payload_common = {
        "topic": state["topic"],
        "plan": plan,
        "evidence_pack": state.get("evidence_pack"),
    }
    return [Send("worker_node", {**payload_common, "task": t}) for t in plan.tasks]


def build_graph() -> Any:
    builder = StateGraph(AgentState)

    builder.add_node("router_node", router_node)
    builder.add_node("research_node", research_node)
    builder.add_node("planner_node", planner_node)
    builder.add_node("worker_node", worker_node)
    builder.add_node("merge_node", merge_node)
    builder.add_node("image_plan_node", image_plan_node)
    builder.add_node("image_gen_node", image_gen_node)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges(
        "router_node",
        _route_after_router,
        {"research_node": "research_node", "planner_node": "planner_node"},
    )
    builder.add_edge("research_node", "planner_node")
    builder.add_conditional_edges("planner_node", _fan_out, ["worker_node"])
    builder.add_edge("worker_node", "merge_node")
    builder.add_edge("merge_node", "image_plan_node")
    builder.add_edge("image_plan_node", "image_gen_node")
    builder.add_edge("image_gen_node", END)

    return builder.compile()


_compiled = None


def run(topic: str) -> dict:
    """Execute the full graph for a topic. Returns final state dict."""
    global _compiled
    if _compiled is None:
        _compiled = build_graph()

    initial: AgentState = {
        "topic": topic,
        "sections": [],
        "decision_log": [],
    }
    log.info("run: topic=%r", topic)
    return _compiled.invoke(initial)
