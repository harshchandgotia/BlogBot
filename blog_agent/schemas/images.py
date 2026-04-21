"""Image planning schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ImageSpec(BaseModel):
    placeholder_tag: str = Field(..., description="e.g. '{{image_1}}'.")
    target_heading: str = Field(..., description="The exact markdown heading (e.g. '## Introduction') after which this image should be inserted.")
    filename: str = Field(..., description="Slugified filename without extension.")
    prompt: str = Field(
        ...,
        description=(
            "Short DuckDuckGo image-search query (2-5 noun-heavy words, no verbs, "
            "no articles). Example: 'transformer attention heatmap'."
        ),
    )
    alt_text: str = Field(..., description="Short alt text / caption.")


class LLMImagePlan(BaseModel):
    images: list[ImageSpec] = Field(default_factory=list, max_length=5)

class GlobalImagePlan(BaseModel):
    markdown_with_placeholders: str
    images: list[ImageSpec] = Field(default_factory=list, max_length=5)
