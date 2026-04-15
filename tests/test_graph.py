"""End-to-end mock graph test (no network calls)."""
from __future__ import annotations

from pathlib import Path

from blog_agent.graph import run


def test_full_mock_graph_produces_markdown(tmp_path, monkeypatch):
    # Redirect output dir so tests don't pollute the repo.
    from blog_agent import config as cfg

    monkeypatch.setattr(cfg.settings, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(cfg.settings, "IMAGE_DIR", tmp_path / "img")
    monkeypatch.setattr(cfg.settings, "HISTORY_DIR", tmp_path / "hist")
    cfg.settings.ensure_dirs()

    state = run("Self-Attention in Transformers")

    assert state.get("plan") is not None
    assert state.get("final_blog_path"), "run must set final_blog_path"

    out = Path(state["final_blog_path"])
    assert out.exists()
    text = out.read_text(encoding="utf-8")

    # Title + all three mock sections present, in plan order.
    assert text.startswith("# ")
    for heading in ("## Introduction", "## Core Mechanics", "## Conclusion"):
        assert heading in text, f"missing {heading}"
    assert text.index("## Introduction") < text.index("## Core Mechanics") < text.index("## Conclusion")

    # Decision log populated.
    log = state.get("decision_log", [])
    joined = " ".join(log)
    for node in ("router", "planner", "merge", "image_plan", "image_gen"):
        assert node in joined, f"decision_log missing {node}"
