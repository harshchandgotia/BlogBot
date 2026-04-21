"""Read/write JSON metadata for past blog generations (Milestone 5)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify

from blog_agent.config import settings
from blog_agent.logger import get_logger

log = get_logger("history")


def save_run(topic: str, final_state: dict) -> Path:
    """Persist a run summary as history/<blog-stem>.json.

    The filename stem is derived from the final blog markdown path so the
    history JSON and the blog `.md` always correlate (H10). Falls back to
    <slug>_<ts> only if final_blog_path is missing.
    """
    blog_path_str = final_state.get("final_blog_path")
    if blog_path_str:
        stem = Path(blog_path_str).stem
        # Timestamp carried inside the record body; try to recover it from
        # the filename for backwards-compatible display in list_runs().
        ts_parts = stem.rsplit("_", 1)
        ts = ts_parts[1] if len(ts_parts) == 2 and "-" in ts_parts[1] else datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = slugify(topic)[:60] or "blog"
        stem = f"{slug}_{ts}"

    path = settings.HISTORY_DIR / f"{stem}.json"

    plan = final_state.get("plan")
    evidence_pack = final_state.get("evidence_pack")
    record = {
        "topic": topic,
        "timestamp": ts,
        "final_blog_path": blog_path_str,
        "plan_summary": {
            "blog_title": plan.blog_title if plan else None,
            "task_titles": [t.title for t in plan.tasks] if plan else [],
        },
        "decision_log": final_state.get("decision_log", []),
        "evidence_pack": evidence_pack.model_dump() if evidence_pack else None,
    }
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    log.info("history: saved %s", path)
    return path


def list_runs() -> list[dict]:
    """Return history records sorted newest-first."""
    records = []
    for p in sorted(settings.HISTORY_DIR.glob("*.json"), reverse=True):
        try:
            records.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:  # noqa: BLE001
            log.warning("skipping unreadable history file %s: %s", p, e)
    return records


def delete_run(record: dict) -> None:
    """Delete a run's markdown file, generated images, and history JSON."""
    import re
    
    # 1. Delete associated images from the markdown payload
    md_path = record.get("final_blog_path")
    if md_path and Path(md_path).exists():
        try:
            content = Path(md_path).read_text(encoding="utf-8")
            for match in re.finditer(r"!\[[^\]]*\]\((images/[^)]+)\)", content):
                rel_img = match.group(1)
                img_path = settings.IMAGE_DIR.parent / rel_img
                if img_path.exists():
                    try:
                        img_path.unlink()
                        log.info("history: deleted image %s", img_path)
                    except Exception as e:
                        log.warning("history: failed to delete image %s: %s", img_path, e)
        except Exception as e:
            log.warning("history: failed to read markdown %s for image cleanup: %s", md_path, e)

        # 2. Delete the markdown file itself
        try:
            Path(md_path).unlink()
            log.info("history: deleted markdown %s", md_path)
        except Exception as e:
            log.warning("history: failed to delete markdown %s: %s", md_path, e)

    # 3. Delete the history JSON file
    topic = record.get("topic", "")
    ts = record.get("timestamp", "")
    slug = slugify(topic)[:60] or "blog"
    json_path = settings.HISTORY_DIR / f"{slug}_{ts}.json"
    
    if json_path.exists():
        try:
            json_path.unlink()
            log.info("history: deleted record %s", json_path)
        except Exception as e:
            log.warning("history: failed to delete JSON record %s: %s", json_path, e)
    else:
        # Fallback searching manually if slug generator changed
        for p in settings.HISTORY_DIR.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("timestamp") == ts and data.get("topic") == topic:
                    p.unlink()
                    log.info("history: deleted record fallback %s", p)
                    break
            except Exception:
                pass
