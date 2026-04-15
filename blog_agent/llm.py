"""Single factory for ChatGroq LLM instances.

All nodes import `get_llm()` from here. Swapping providers means editing this file only.
"""
from __future__ import annotations

from langchain_groq import ChatGroq

from blog_agent.config import settings


def get_llm(temperature: float | None = None) -> ChatGroq:
    """Return a configured ChatGroq instance."""
    return ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        max_retries=settings.LLM_MAX_RETRIES,
    )
