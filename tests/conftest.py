"""Test-wide fixtures: force all node mocks on so no network is called."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _force_mock_mode(monkeypatch):
    """Flip every node's USE_MOCK flag to True for all tests.

    Tests that explicitly want to exercise the real path can override this
    by re-monkeypatching the attribute back to False.
    """
    os.environ["BLOG_AGENT_PLANNER_MOCK"] = "1"
    os.environ["BLOG_AGENT_WORKER_MOCK"] = "1"
    os.environ["BLOG_AGENT_ROUTER_MOCK"] = "1"
    os.environ["BLOG_AGENT_RESEARCH_MOCK"] = "1"
    os.environ["BLOG_AGENT_IMAGE_PLAN_MOCK"] = "1"
    os.environ["BLOG_AGENT_IMAGE_GEN_MOCK"] = "1"

    # Force re-evaluation by patching module attrs (modules may already be imported).
    import blog_agent.nodes.planner as planner_mod
    import blog_agent.nodes.reducer.image_gen as image_gen_mod
    import blog_agent.nodes.reducer.image_plan as image_plan_mod
    import blog_agent.nodes.research as research_mod
    import blog_agent.nodes.router as router_mod
    import blog_agent.nodes.worker as worker_mod

    monkeypatch.setattr(planner_mod, "USE_MOCK", True, raising=False)
    monkeypatch.setattr(worker_mod, "USE_MOCK", True, raising=False)
    monkeypatch.setattr(router_mod, "USE_MOCK", True, raising=False)
    monkeypatch.setattr(research_mod, "USE_MOCK", True, raising=False)
    monkeypatch.setattr(image_plan_mod, "USE_MOCK", True, raising=False)
    monkeypatch.setattr(image_gen_mod, "USE_MOCK", True, raising=False)
    yield
