"""Image planning node - inserts {{image_N}} placeholders + SDXL prompts."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from blog_agent.llm import get_llm
from blog_agent.logger import get_logger
from blog_agent.prompts.image_planner import (
    IMAGE_PLANNER_SYSTEM,
    IMAGE_PLANNER_USER_TEMPLATE,
)
from blog_agent.schemas import AgentState, GlobalImagePlan, LLMImagePlan
from tenacity import retry, stop_after_attempt, wait_exponential

log = get_logger("image_plan")

USE_MOCK = os.environ.get("BLOG_AGENT_IMAGE_PLAN_MOCK", "0") == "1"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _real_plan(merged: str, blog_title: str, audience: str) -> LLMImagePlan:
    llm = get_llm(temperature=0.4).with_structured_output(LLMImagePlan)
    messages = [
        SystemMessage(content=IMAGE_PLANNER_SYSTEM),
        HumanMessage(
            content=IMAGE_PLANNER_USER_TEMPLATE.format(
                blog_title=blog_title,
                audience=audience,
                merged_blog=merged,
            )
        ),
    ]
    result = llm.invoke(messages)
    assert isinstance(result, LLMImagePlan), "LLMOutput missing"
    return result


def image_plan_node(state: AgentState) -> dict:
    merged = state.get("merged_blog") or ""
    plan = state.get("plan")
    blog_title = plan.blog_title if plan else "Blog"
    audience = plan.audience if plan else "general readers"
    log.info("image_plan: merged %d chars mock=%s", len(merged), USE_MOCK)

    if USE_MOCK:
        plan_output = LLMImagePlan(images=[])
    else:
        try:
            plan_output = _real_plan(merged, blog_title, audience)
        except Exception as e:  # noqa: BLE001
            log.warning("image_plan LLM failed (%s) -> skipping images", e)
            plan_output = LLMImagePlan(images=[])

    # Insert the placeholder tags manually into the merged markdown
    result_markdown = merged
    kept = []
    for spec in plan_output.images:
        target = spec.target_heading.strip()
        if target and target in result_markdown:
            # Insert right below the target heading
            parts = result_markdown.split(target, 1)
            result_markdown = f"{parts[0]}{target}\n\n{spec.placeholder_tag}\n{parts[1]}"
            kept.append(spec)
            
    if len(kept) != len(plan_output.images):
        log.info("image_plan: dropped %d specs missing target heading", len(plan_output.images) - len(kept))
    
    result = GlobalImagePlan(markdown_with_placeholders=result_markdown, images=kept)

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "image_plan": result,
        "decision_log": [f"{ts} image_plan -> {len(result.images)} images planned"],
    }
