"""Merge node - joins parallel worker sections in plan order.

Each worker prepends `<!--section:{id}-->` so we can restore original ordering
regardless of the order workers completed in.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from blog_agent.logger import get_logger
from blog_agent.schemas import AgentState

log = get_logger("merge")

_TAG_RE = re.compile(r"<!--section:(.*?)-->\s*\n?")


def _extract_id(section_md: str) -> str | None:
    m = _TAG_RE.match(section_md)
    return m.group(1) if m else None


def _strip_tag(section_md: str) -> str:
    return _TAG_RE.sub("", section_md, count=1).lstrip("\n")


def merge_node(state: AgentState) -> dict:
    plan = state["plan"]
    sections = state.get("sections", []) or []
    assert plan is not None, "merge_node requires a plan"
    log.info("merge: %d sections", len(sections))

    # Build id -> section map.
    by_id: dict[str, str] = {}
    orphans: list[str] = []
    for s in sections:
        sid = _extract_id(s)
        if sid is None:
            orphans.append(_strip_tag(s))
        else:
            by_id[sid] = _strip_tag(s)

    ordered: list[str] = []
    for task in plan.tasks:
        piece = by_id.pop(task.id, None)
        if piece is not None:
            ordered.append(piece)
    # Any leftovers (shouldn't happen, but be forgiving)
    ordered.extend(by_id.values())
    ordered.extend(orphans)

    title_line = f"# {plan.blog_title}\n"
    merged = title_line + "\n" + "\n\n".join(s.rstrip() for s in ordered) + "\n"

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "merged_blog": merged,
        "decision_log": [f"{ts} merge -> {len(ordered)} sections joined"],
    }
