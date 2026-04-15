"""Tests for research node: dedup + mock fallthrough."""
from __future__ import annotations

from blog_agent.nodes.research import _dedup, research_node
from blog_agent.schemas import EvidenceItem, RouterDecision


def test_dedup_by_url_strips_fragments_and_trailing_slash():
    items = [
        EvidenceItem(title="A", url="https://example.com/page", snippet="s"),
        EvidenceItem(title="A2", url="https://example.com/page#frag", snippet="s"),
        EvidenceItem(title="A3", url="https://example.com/page/", snippet="s"),
        EvidenceItem(title="B", url="https://example.com/other", snippet="s"),
    ]
    out = _dedup(items)
    urls = [i.url for i in out]
    # First form kept; later duplicates dropped.
    assert urls == ["https://example.com/page", "https://example.com/other"]


def test_research_node_mock_returns_empty_pack():
    # conftest forces USE_MOCK=True, so research_node should not hit the network.
    state = {
        "topic": "t",
        "router_decision": RouterDecision(
            needs_research=True, mode="open_book", queries=["q1", "q2"]
        ),
    }
    out = research_node(state)
    assert out["evidence_pack"].items == []
