"""History persistence: save_run + list_runs."""
from __future__ import annotations

from blog_agent.history import list_runs, save_run
from blog_agent.schemas import Plan, Task


def test_save_and_list_roundtrip(tmp_path, monkeypatch):
    from blog_agent import config as cfg

    monkeypatch.setattr(cfg.settings, "HISTORY_DIR", tmp_path / "hist")
    cfg.settings.ensure_dirs()

    plan = Plan(
        blog_title="Hello",
        audience="devs",
        tone="clear",
        tasks=[
            Task(id="s1", title="Intro", goal="g", bullets=["a", "b", "c"], target_words=180),
            Task(id="s2", title="Body1", goal="g", bullets=["a", "b", "c"], target_words=350),
            Task(id="s3", title="Body2", goal="g", bullets=["a", "b", "c"], target_words=350),
            Task(id="s4", title="Body3", goal="g", bullets=["a", "b", "c"], target_words=300),
            Task(id="s5", title="Conclusion", goal="g", bullets=["a", "b", "c"], target_words=160),
        ],
    )
    state = {
        "topic": "hello-world",
        "final_blog_path": str(tmp_path / "out" / "hello-world_20260101-000000.md"),
        "plan": plan,
        "decision_log": ["line1", "line2"],
    }
    # The path stem is derived from final_blog_path (H10), so create that file's
    # parent dir; the file itself doesn't need to exist for save_run.
    (tmp_path / "out").mkdir(parents=True, exist_ok=True)
    path = save_run("hello-world", state)
    assert path.exists()

    records = list_runs()
    assert len(records) == 1
    rec = records[0]
    assert rec["topic"] == "hello-world"
    assert rec["plan_summary"]["blog_title"] == "Hello"
    assert rec["plan_summary"]["task_titles"] == ["Intro", "Body1", "Body2", "Body3", "Conclusion"]
    assert rec["decision_log"] == ["line1", "line2"]
