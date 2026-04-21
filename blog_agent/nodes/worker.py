"""Worker node - writes one section via Groq. Invoked in parallel via Send."""
from __future__ import annotations

import os

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from blog_agent.llm import get_llm
from blog_agent.logger import get_logger
from blog_agent.prompts.worker import (
    WORKER_SYSTEM,
    WORKER_USER_TEMPLATE,
    format_bullets,
    format_evidence_block,
)
from blog_agent.schemas import EvidencePack, Plan, Task

log = get_logger("worker")

# Tests flip this to True via monkeypatch to avoid network calls.
USE_MOCK = os.environ.get("BLOG_AGENT_WORKER_MOCK", "0") == "1"


def _mock_section(task: Task) -> str:
    bullets_md = "\n".join(f"- {b}" for b in task.bullets)
    return (
        f"## {task.title}\n\n"
        f"*[mock section - {task.target_words} words target]*\n\n"
        f"{task.goal}\n\n"
        f"{bullets_md}\n"
    )


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60))
def _real_section(
    task: Task,
    topic: str,
    plan: Plan,
    evidence_compact: str,
) -> str:
    llm = get_llm(temperature=0.5)
    messages = [
        SystemMessage(content=WORKER_SYSTEM),
        HumanMessage(
            content=WORKER_USER_TEMPLATE.format(
                topic=topic,
                blog_title=plan.blog_title,
                audience=plan.audience,
                tone=plan.tone,
                title=task.title,
                goal=task.goal,
                bullets_formatted=format_bullets(task.bullets),
                target_words=task.target_words,
                requires_code=task.requires_code,
                requires_citation=task.requires_citation,
                evidence_block=format_evidence_block(evidence_compact, task.requires_citation),
            )
        ),
    ]
    result = llm.invoke(messages)
    text = (result.content or "").strip()
    # Enforce leading `## title` heading - prepend if the LLM forgot.
    if not text.lstrip().startswith("## "):
        text = f"## {task.title}\n\n{text}"
    return text


def worker_node(payload: dict) -> dict:
    task: Task = payload["task"]
    topic: str = payload["topic"]
    plan: Plan = payload["plan"]
    evidence: EvidencePack | None = payload.get("evidence_pack")
    evidence_compact = evidence.compact_context() if evidence else ""
    log.info("worker: section=%r", task.title)

    if USE_MOCK:
        section_md = _mock_section(task)
    else:
        section_md = _real_section(task, topic, plan, evidence_compact)

    tagged = f"<!--section:{task.id}-->\n{section_md}"
    return {"sections": [tagged]}
