"""Image gen node: fallback behavior + placeholder substitution."""
from __future__ import annotations

from pathlib import Path

from blog_agent.nodes.reducer.image_gen import image_gen_node
from blog_agent.schemas import GlobalImagePlan, ImageSpec


def test_image_gen_fallback_replaces_placeholders_when_gen_fails(tmp_path, monkeypatch):
    from blog_agent import config as cfg

    monkeypatch.setattr(cfg.settings, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(cfg.settings, "IMAGE_DIR", tmp_path / "img")
    cfg.settings.ensure_dirs()

    md = "# Hi\n\n{{image_1}}\n\nThe end.\n"
    plan = GlobalImagePlan(
        markdown_with_placeholders=md,
        images=[
            ImageSpec(
                placeholder_tag="{{image_1}}",
                target_heading="## Hi",
                filename="example",
                prompt="an example image",
                alt_text="example illustration",
            )
        ],
    )
    state = {"image_plan": plan, "topic": "demo"}
    out = image_gen_node(state)

    path = Path(out["final_blog_path"])
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    # Placeholder replaced by italic fallback note (USE_MOCK -> always None img).
    assert "{{image_1}}" not in content
    assert "Image unavailable" in content


def test_image_gen_with_successful_generation_writes_embed(tmp_path, monkeypatch):
    from blog_agent import config as cfg
    import blog_agent.nodes.reducer.image_gen as mod

    monkeypatch.setattr(cfg.settings, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(cfg.settings, "IMAGE_DIR", tmp_path / "img")
    cfg.settings.ensure_dirs()

    # Simulate a successful HF generation.
    fake_path = tmp_path / "img" / "example_stub.png"
    fake_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)

    monkeypatch.setattr(mod, "_generate_image", lambda spec: fake_path)

    md = "# Hi\n\n{{image_1}}\n\nThe end.\n"
    plan = GlobalImagePlan(
        markdown_with_placeholders=md,
        images=[
            ImageSpec(
                placeholder_tag="{{image_1}}",
                target_heading="## Hi",
                filename="example",
                prompt="x",
                alt_text="example",
            )
        ],
    )
    out = image_gen_node({"image_plan": plan, "topic": "demo"})
    content = Path(out["final_blog_path"]).read_text(encoding="utf-8")
    assert "{{image_1}}" not in content
    assert "![example](images/example_stub.png)" in content
