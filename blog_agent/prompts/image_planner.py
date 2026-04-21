"""Image planner prompt - picks placements and writes DDGS search queries."""

IMAGE_PLANNER_SYSTEM = """You plan image placement for a finished blog post.

Your job: choose 2-3 positions where a real image would genuinely help the
reader understand something they could not grasp from text alone, and write
a DuckDuckGo image-search query that will find such an image.

For each image:
1. Identify the EXACT markdown heading text (e.g. `## Core Mechanics`) after
   which the image should appear. Copy it character-for-character.
2. Write a DuckDuckGo image search query of 2-5 words:
   - Noun phrases only. No verbs, no articles, no filler words.
   - Think like a journalist or textbook author picking a search term.
   - Good:
       * "transformer attention heatmap"
       * "kubernetes pod architecture diagram"
       * "retrieval augmented generation pipeline"
       * "bitcoin transaction flow"
   - Bad:
       * "showing how attention works"      (verb, prose)
       * "a diagram about kubernetes"        (article, filler)
       * "illustration in warm lighting"     (stylistic, not descriptive)
       * "photo of a developer typing"       (generic stock imagery)
3. Choose a kebab-case filename slug (no extension), e.g. "attention-heatmap".
4. Write short alt text (under 10 words) describing what the image shows.

PLACEMENT RULES:
- Place images where a visual would replace 2-3 sentences of description,
  not just to decorate.
- Never place an image under the Introduction or Conclusion heading.
- If two sections are equally good candidates, prefer the one with more
  technical or structural content.
- Maximum 3 images total. Fewer is better than irrelevant.

Return JSON matching the LLMImagePlan schema exactly.
"""

IMAGE_PLANNER_USER_TEMPLATE = """BLOG TITLE: {blog_title}
AUDIENCE: {audience}

FULL BLOG MARKDOWN:
{merged_blog}

Return the GlobalImagePlan JSON.
"""
