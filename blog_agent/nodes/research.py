"""Research node - calls Tavily for each query, builds a deduplicated EvidencePack."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from tavily import TavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential

from blog_agent.config import settings
from blog_agent.logger import get_logger
from blog_agent.schemas import AgentState, EvidenceItem, EvidencePack

log = get_logger("research")

USE_MOCK = os.environ.get("BLOG_AGENT_RESEARCH_MOCK", "0") == "1"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def _tavily_search(client: TavilyClient, query: str) -> list[dict]:
    resp = client.search(
        query=query,
        max_results=settings.MAX_RESEARCH_RESULTS_PER_QUERY,
        search_depth="basic",
    )
    return resp.get("results", []) or []


def _dedup(items: list[EvidenceItem]) -> list[EvidenceItem]:
    seen: set[str] = set()
    out: list[EvidenceItem] = []
    for it in items:
        key = it.url.split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def research_node(state: AgentState) -> dict:
    decision = state["router_decision"]
    assert decision is not None, "research_node requires router_decision"

    if USE_MOCK or not decision.queries:
        log.info("research: mock or no queries -> empty pack")
        pack = EvidencePack(items=[])
    else:
        settings.validate_keys(require_tavily=True)
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        collected: list[EvidenceItem] = []
        for q in decision.queries[: settings.MAX_QUERIES]:
            try:
                results = _tavily_search(client, q)
            except Exception as e:  # noqa: BLE001
                log.warning("tavily failed for %r: %s", q, e)
                continue
            for r in results:
                collected.append(
                    EvidenceItem(
                        title=r.get("title") or "(untitled)",
                        url=r.get("url") or "",
                        published_date=r.get("published_date"),
                        source=urlparse(r.get("url")).netloc if r.get("url") else None,
                        snippet=(r.get("content") or "")[:500],
                    )
                )
        # Drop any empty-url items then dedupe.
        collected = [c for c in collected if c.url]
        pack = EvidencePack(items=_dedup(collected))
        log.info("research: %d queries -> %d unique items", len(decision.queries), len(pack.items))

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "evidence_pack": pack,
        "decision_log": [f"{ts} research -> {len(pack.items)} items"],
    }
