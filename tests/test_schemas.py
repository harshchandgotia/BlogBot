"""Validation tests for Pydantic schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from blog_agent.schemas import (
    EvidenceItem,
    EvidencePack,
    GlobalImagePlan,
    ImageSpec,
    Plan,
    RouterDecision,
    Task,
)


def test_task_valid():
    t = Task(
        id="s1",
        title="Intro",
        goal="Reader learns X.",
        bullets=["a", "b", "c"],
        target_words=180,
    )
    assert t.requires_research is False


def test_task_rejects_too_few_bullets():
    with pytest.raises(ValidationError):
        Task(id="s1", title="Intro", goal="g", bullets=["only one"], target_words=180)


def test_task_rejects_out_of_range_words():
    with pytest.raises(ValidationError):
        Task(id="s1", title="Intro", goal="g", bullets=["a", "b"], target_words=10)


def test_plan_requires_tasks():
    with pytest.raises(ValidationError):
        Plan(
            blog_title="T",
            audience="a",
            tone="clear",
            tasks=[],  # empty -> violates min_length
        )


def test_router_decision_defaults():
    d = RouterDecision(needs_research=False, mode="closed_book")
    assert d.queries == []


def test_evidence_pack_compact_context():
    pack = EvidencePack(
        items=[
            EvidenceItem(title="A", url="https://a.com", snippet="snip-a"),
            EvidenceItem(title="B", url="https://b.com", snippet="snip-b"),
        ]
    )
    out = pack.compact_context()
    assert "[1] A" in out and "[2] B" in out
    assert "https://a.com" in out


def test_image_plan_empty_valid():
    p = GlobalImagePlan(markdown_with_placeholders="# Hello", images=[])
    assert p.images == []


def test_image_spec_valid():
    s = ImageSpec(
        placeholder_tag="{{image_1}}",
        target_heading="## Intro",
        filename="foo",
        prompt="A cat on a table, digital illustration.",
        alt_text="cat",
    )
    assert s.placeholder_tag == "{{image_1}}"
