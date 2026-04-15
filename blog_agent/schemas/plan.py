"""Blog plan + task schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single section of the blog, assigned to one worker."""

    id: str = Field(..., description="Short stable id, e.g. 's1', 's2'.")
    title: str = Field(..., description="Section heading (no leading '#').")
    goal: str = Field(..., description="One-sentence outcome this section should deliver.")
    bullets: list[str] = Field(
        ...,
        description="3-5 concrete sub-points the worker must cover.",
        min_length=2,
        max_length=8,
    )
    target_words: int = Field(..., ge=80, le=800)
    tags: list[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citation: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str
    audience: str = Field(..., description="Who this blog is for (e.g. 'ML engineers').")
    tone: str = Field(..., description="e.g. 'technical', 'casual explainer', 'formal whitepaper'.")
    kind: Literal["explainer", "news", "tutorial", "analysis", "listicle"] = "explainer"
    constraints: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(..., min_length=3, max_length=12)
