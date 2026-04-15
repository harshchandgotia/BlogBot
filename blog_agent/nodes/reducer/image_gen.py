"""Image generation via Hugging Face SDXL + final markdown write."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from ddgs import DDGS
from slugify import slugify
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from blog_agent.config import settings
from blog_agent.logger import get_logger
from blog_agent.schemas import AgentState, ImageSpec

log = get_logger("image_gen")

USE_MOCK = os.environ.get("BLOG_AGENT_IMAGE_GEN_MOCK", "0") == "1"


def _fetch_url(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image/"):
            return None
        return r.content
    except Exception as e: # noqa: BLE001
        log.warning("Fetch failed %s: %s", url, e)
        return None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def _search_and_download_image(prompt: str) -> bytes:
    with DDGS() as ddgs:
        results = list(ddgs.images(prompt, max_results=5, safesearch="on"))
        if not results:
            raise RuntimeError(f"No image results found for: {prompt}")
            
        for res in results:
            url = res.get("image")
            if not url:
                continue
            content = _fetch_url(url)
            if content:
                log.info("Successfully fetched %s", url)
                return content
                
    raise RuntimeError(f"All DDGS image URLs failed to download for: {prompt}")


def _generate_image(spec: ImageSpec) -> Path | None:
    """Generate one image; returns path on success, None on graceful failure."""
    if USE_MOCK:
        return None
    try:
        png = _search_and_download_image(spec.prompt)
    except RetryError as e:
        log.warning("DDGS retries exhausted for %s: %s", spec.placeholder_tag, e)
        return None
    except Exception as e:  # noqa: BLE001
        log.warning("DDGS search failed for %s: %s", spec.placeholder_tag, e)
        return None

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    fname = f"{slugify(spec.filename)[:60] or 'image'}_{ts}.png"
    out = settings.IMAGE_DIR / fname
    out.write_bytes(png)
    log.info("image_gen: saved %s (%d bytes)", out.name, len(png))
    return out


def _fallback_replace(markdown: str, spec: ImageSpec, reason: str) -> str:
    note = f"*[Image unavailable: {spec.alt_text} - {reason}]*"
    return markdown.replace(spec.placeholder_tag, note)


def _write_final(markdown: str, topic: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = slugify(topic)[:60] or "blog"
    out_path = settings.OUTPUT_DIR / f"{slug}_{ts}.md"
    out_path.write_text(markdown, encoding="utf-8")
    return out_path


def image_gen_node(state: AgentState) -> dict:
    plan = state["image_plan"]
    topic = state["topic"]
    assert plan is not None, "image_gen requires image_plan"

    markdown = plan.markdown_with_placeholders
    log.info("image_gen: %d specs mock=%s", len(plan.images), USE_MOCK)

    successes = 0
    for spec in plan.images:
        img_path = _generate_image(spec)
        if img_path is None:
            markdown = _fallback_replace(markdown, spec, "generation failed")
            continue
        # Reference relative to the markdown file (both live in repo root subdirs).
        rel = Path("images") / img_path.name
        embed = f"![{spec.alt_text}]({rel.as_posix()})"
        markdown = markdown.replace(spec.placeholder_tag, embed)
        successes += 1

    out_path = _write_final(markdown, topic)
    log.info("image_gen: wrote %s (%d/%d images embedded)", out_path, successes, len(plan.images))

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "final_blog_path": str(out_path),
        "decision_log": [
            f"{ts} image_gen -> wrote {out_path.name} ({successes}/{len(plan.images)} images)"
        ],
    }
