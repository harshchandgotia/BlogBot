"""Shared agent state passed through the LangGraph state machine."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from blog_agent.schemas.images import GlobalImagePlan
from blog_agent.schemas.plan import Plan
from blog_agent.schemas.research import EvidencePack, RouterDecision


class AgentState(TypedDict, total=False):
    topic: str
    router_decision: RouterDecision | None
    evidence_pack: EvidencePack | None
    plan: Plan | None
    # sections are appended in parallel by worker nodes -> reducer must allow concat
    sections: Annotated[list[str], operator.add]
    merged_blog: str | None
    image_plan: GlobalImagePlan | None
    final_blog_path: str | None
    decision_log: Annotated[list[str], operator.add]
