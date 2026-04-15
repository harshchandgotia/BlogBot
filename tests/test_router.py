"""Router node mock behavior + conditional-edge routing."""
from __future__ import annotations

from blog_agent.graph import _route_after_router, run
from blog_agent.nodes.router import router_node
from blog_agent.schemas import RouterDecision


def test_router_mock_returns_closed_book():
    out = router_node({"topic": "anything"})
    d = out["router_decision"]
    assert d.mode == "closed_book"
    assert d.needs_research is False


def test_route_after_router_picks_research_when_needed():
    state = {
        "router_decision": RouterDecision(
            needs_research=True, mode="open_book", queries=["q"]
        )
    }
    assert _route_after_router(state) == "research_node"


def test_route_after_router_picks_planner_otherwise():
    state = {
        "router_decision": RouterDecision(needs_research=False, mode="closed_book")
    }
    assert _route_after_router(state) == "planner_node"


def test_full_graph_routes_through_research_when_forced(tmp_path, monkeypatch):
    """Force router to say needs_research=True; ensure research_node ran."""
    from blog_agent import config as cfg
    import blog_agent.nodes.router as router_mod

    monkeypatch.setattr(cfg.settings, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(cfg.settings, "IMAGE_DIR", tmp_path / "img")
    monkeypatch.setattr(cfg.settings, "HISTORY_DIR", tmp_path / "hist")
    cfg.settings.ensure_dirs()

    def fake_mock():
        return RouterDecision(
            needs_research=True, mode="open_book", queries=["a", "b"], reasoning="forced"
        )

    monkeypatch.setattr(router_mod, "_mock_decision", fake_mock)

    state = run("fresh topic")
    log = " ".join(state.get("decision_log", []))
    assert "research" in log
    assert state["router_decision"].mode == "open_book"
