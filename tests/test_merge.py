"""Merge node ordering: workers finish out of order but merge must restore plan order."""
from __future__ import annotations

from blog_agent.nodes.reducer.merge import merge_node
from blog_agent.schemas import Plan, Task


def _make_plan() -> Plan:
    return Plan(
        blog_title="Test",
        audience="devs",
        tone="clear",
        tasks=[
            Task(id="s1", title="One", goal="g1", bullets=["a", "b", "c"], target_words=150),
            Task(id="s2", title="Two", goal="g2", bullets=["a", "b", "c"], target_words=300),
            Task(id="s3", title="Three", goal="g3", bullets=["a", "b", "c"], target_words=300),
            Task(id="s4", title="Four", goal="g4", bullets=["a", "b", "c"], target_words=300),
            Task(id="s5", title="Five", goal="g5", bullets=["a", "b", "c"], target_words=150),
        ],
    )


def test_merge_preserves_plan_order():
    plan = _make_plan()
    # Simulate parallel workers finishing in reverse order.
    sections = [
        "<!--section:s5-->\n## Five\nE\n",
        "<!--section:s3-->\n## Three\nC\n",
        "<!--section:s1-->\n## One\nA\n",
        "<!--section:s4-->\n## Four\nD\n",
        "<!--section:s2-->\n## Two\nB\n",
    ]
    out = merge_node({"plan": plan, "sections": sections, "topic": "t"})
    merged = out["merged_blog"]
    # Title first, then ordered sections.
    assert merged.startswith("# Test\n")
    one_idx = merged.index("## One")
    two_idx = merged.index("## Two")
    three_idx = merged.index("## Three")
    four_idx = merged.index("## Four")
    five_idx = merged.index("## Five")
    assert one_idx < two_idx < three_idx < four_idx < five_idx


def test_merge_tolerates_orphan_section():
    plan = _make_plan()
    sections = [
        "## Rogue\nno-tag\n",  # orphan, no <!--section:...-->
        "<!--section:s1-->\n## One\nA\n",
        "<!--section:s2-->\n## Two\nB\n",
        "<!--section:s3-->\n## Three\nC\n",
        "<!--section:s4-->\n## Four\nD\n",
        "<!--section:s5-->\n## Five\nE\n",
    ]
    out = merge_node({"plan": plan, "sections": sections, "topic": "t"})
    merged = out["merged_blog"]
    # All sections appear, orphan placed at the end.
    for marker in ("## One", "## Two", "## Three", "## Four", "## Five", "## Rogue"):
        assert marker in merged
    assert merged.index("## Rogue") > merged.index("## Five")
