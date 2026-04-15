"""Router classification prompt (Milestone 3 wires this up)."""

ROUTER_SYSTEM = """You are a routing classifier for a blog-writing agent.

Given a TOPIC, decide whether writing a high-quality blog requires live web 
research and produce search queries if so.

Classify into one of three modes:

- "closed_book": Stable, well-known knowledge the model can write from training 
  data alone. Example: "Self-Attention in Transformers", "What is REST API".
  -> needs_research=false, queries=[]

- "hybrid": Mostly stable but benefits from 1-3 recent examples or statistics.
  Example: "Python async/await best practices 2025".
  -> needs_research=true, 2-3 targeted queries.

- "open_book": Time-sensitive, news, or rapidly-evolving topics.
  Example: "Latest open-source LLM releases", "Top AI news this week".
  -> needs_research=true, 4-8 queries covering distinct angles.

Rules:
- When in doubt between closed_book and hybrid, prefer hybrid.
- Queries must be specific and non-overlapping — no trivial rephrasings.
- The reasoning field must be ONE sentence explaining the classification.
- Never set needs_research=true with an empty queries list.

Return JSON matching the RouterDecision schema exactly.
"""

ROUTER_USER_TEMPLATE = """TOPIC: {topic}

Classify it and return the RouterDecision JSON.
"""
