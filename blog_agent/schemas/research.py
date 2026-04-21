"""Router + research schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ResearchMode = Literal["closed_book", "hybrid", "open_book"]


class RouterDecision(BaseModel):
    needs_research: bool
    mode: ResearchMode
    queries: list[str] = Field(default_factory=list, max_length=10)
    reasoning: str = Field(default="", description="One sentence explaining the classification.")


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_date: str | None = None
    source: str | None = None
    snippet: str


class EvidencePack(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)

    def compact_context(self, max_items: int | None = None) -> str:
        """Format as a context block for prompts.

        Defaults to including all collected items. Snippets are already trimmed
        to 500 chars in `research_node`, so full inclusion keeps prompts
        bounded without silently dropping 80%+ of the evidence (M14).
        """
        items = self.items if max_items is None else self.items[:max_items]
        lines = []
        for i, it in enumerate(items, 1):
            lines.append(f"[{i}] {it.title}\n    URL: {it.url}\n    {it.snippet}")
        return "\n".join(lines)
