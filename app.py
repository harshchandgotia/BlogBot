"""Streamlit frontend for the Blog Bot."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import streamlit as st

from blog_agent.config import settings
from blog_agent.graph import build_graph
from blog_agent.history import list_runs, save_run, delete_run
from blog_agent.schemas import AgentState, EvidencePack

st.set_page_config(page_title="Blog Bot", page_icon=":memo:", layout="wide")


# ---------- session state ----------
if "final_state" not in st.session_state:
    st.session_state.final_state = None
if "compiled" not in st.session_state:
    st.session_state.compiled = build_graph()


# ---------- sidebar ----------
with st.sidebar:
    st.header("Blog Bot")
    topic = st.text_input(
        "Topic",
        placeholder="e.g. Self-Attention in Transformers",
        key="topic_input",
    )
    generate = st.button("Generate Blog", type="primary", use_container_width=True)

    st.divider()
    st.subheader("History")
    records = list_runs()
    if not records:
        st.caption("(No runs yet.)")
    else:
        for rec in records[:20]:
            col_btn, col_del = st.columns([5, 1])
            label = f"{rec.get('topic', '?')} · {rec.get('timestamp', '')}"
            with col_btn:
                if st.button(label, key=f"hist_{rec.get('timestamp', '')}_{rec.get('topic')}", use_container_width=True):
                    path = rec.get("final_blog_path")
                    if path and Path(path).exists():
                        # Reconstruct evidence_pack from persisted dict
                        raw_pack = rec.get("evidence_pack")
                        evidence_pack = EvidencePack(**raw_pack) if raw_pack else None
                        st.session_state.final_state = {
                            "topic": rec.get("topic"),
                            "timestamp": rec.get("timestamp"),
                            "final_blog_path": path,
                            "decision_log": rec.get("decision_log", []),
                            "plan": None,  # plan object not persisted; we only have summary
                            "plan_summary": rec.get("plan_summary"),
                            "evidence_pack": evidence_pack,
                        }
                    else:
                        st.warning(f"File missing: {path}")
            
            with col_del:
                if st.button("❌", key=f"del_{rec.get('timestamp', '')}_{rec.get('topic')}"):
                    delete_run(rec)
                    if st.session_state.final_state and st.session_state.final_state.get("final_blog_path") == rec.get("final_blog_path"):
                        st.session_state.final_state = None
                    st.rerun()


# ---------- main panel ----------
st.title("Blog Bot")

if generate and topic.strip():
    initial: AgentState = {"topic": topic.strip(), "sections": [], "decision_log": []}

    status = st.status("Running agent graph...", expanded=True)

    with status:
        progress_placeholder = st.empty()
        final_state: dict | None = None
        try:
            # stream_mode="values" yields the cumulative state after each super-step.
            # The last emission is the final state - single pass, no re-execution.
            for cum_state in st.session_state.compiled.stream(initial, stream_mode="values"):
                final_state = cum_state
                log_lines = cum_state.get("decision_log", []) if cum_state else []
                if log_lines:
                    # Show the last few node entries so the user sees progress.
                    recent = log_lines[-6:]
                    progress_placeholder.write("\n".join(f"• {ln}" for ln in recent))
            assert final_state is not None
            save_run(topic.strip(), final_state)
            st.session_state.final_state = final_state
            status.update(label="Done", state="complete")
        except Exception as e:  # noqa: BLE001
            status.update(label=f"Failed: {e}", state="error")
            st.exception(e)

# ---------- render output ----------
state = st.session_state.final_state
if state:
    path = state.get("final_blog_path")
    if path and Path(path).exists():
        md_text = Path(path).read_text(encoding="utf-8")
        
        # Rewrite image paths to base64 for Streamlit rendering
        def _base64_replacer(match):
            alt_text, rel_img = match.group(1), match.group(2)
            img_path = settings.IMAGE_DIR.parent / rel_img
            if img_path.exists():
                b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
                return f"![{alt_text}](data:image/png;base64,{b64})"
            return match.group(0)
            
        render_md = re.sub(r"!\[([^\]]*)\]\((images/[^)]+)\)", _base64_replacer, md_text)

        col_main, col_side = st.columns([3, 1])

        with col_main:
            st.markdown(render_md, unsafe_allow_html=True)

        with col_side:
            st.download_button(
                "Download Blog (.md)",
                data=md_text,
                file_name=Path(path).name,
                mime="text/markdown",
                use_container_width=True,
            )

        st.divider()

        plan = state.get("plan")
        with st.expander("Plan Details", expanded=False):
            if plan:
                st.write(f"**Title:** {plan.blog_title}")
                st.write(f"**Audience:** {plan.audience}")
                st.write(f"**Tone:** {plan.tone}")
                st.write(f"**Kind:** {plan.kind}")
                for t in plan.tasks:
                    st.markdown(f"**{t.id} — {t.title}** ({t.target_words}w)")
                    st.caption(t.goal)
                    for b in t.bullets:
                        st.markdown(f"  - {b}")
            elif state.get("plan_summary"):
                summary = state["plan_summary"]
                st.write(f"**Title:** {summary.get('blog_title')}")
                for title in summary.get("task_titles", []):
                    st.markdown(f"- {title}")
            else:
                st.caption("(No plan available.)")

        with st.expander("Sources", expanded=False):
            pack = state.get("evidence_pack")
            if pack and pack.items:
                for i, it in enumerate(pack.items, 1):
                    st.markdown(f"{i}. [{it.title}]({it.url})")
                    if it.snippet:
                        clean_snippet = it.snippet[:200].replace("#", "").replace("\n", " ").strip()
                        st.caption(clean_snippet)
            else:
                st.caption("(No external sources - closed-book topic.)")

        with st.expander("Decision Log", expanded=False):
            for line in state.get("decision_log", []):
                st.code(line, language="text")

        with st.expander("Image Gallery", expanded=False):
            img_plan = state.get("image_plan")
            if img_plan and img_plan.images:
                for spec in img_plan.images:
                    img_path = settings.IMAGE_DIR / f"{spec.filename}.png"
                    matches = list(settings.IMAGE_DIR.glob(f"{spec.filename}*.png"))
                    if matches:
                        st.image(str(matches[-1]), caption=spec.alt_text, use_container_width=True)
                    else:
                        st.caption(f"(No image generated for {spec.placeholder_tag})")
            else:
                st.caption("(No images in this run.)")
    else:
        st.warning("Final blog file not found on disk.")
else:
    st.info("Enter a topic in the sidebar and click *Generate Blog* to begin.")
