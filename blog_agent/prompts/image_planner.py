"""Image planner prompt - inserts placeholders + writes SDXL prompts."""

IMAGE_PLANNER_SYSTEM = """You plan image placement for a finished blog post.

Given the full blog markdown, insert 2-3 {{image_N}} placeholder tokens at
positions where a specific real-world image or diagram would genuinely aid understanding.
For each placeholder, write a highly targeted search engine query (to be used in DuckDuckGo).

Rules:
1. Identify 2-3 positions where an image would be most effective.
2. Provide the EXACT text of the markdown heading (`target_heading`) that immediately precedes where you want the image to go (e.g. `## Core Mechanics`).
3. Use placeholder tags exactly of the form `{{image_1}}`, `{{image_2}}`, ...
4. Image queries (`prompt`) should be:
   - Specific and concise search keywords (nouns, concrete objects)
   - Optimized for an image search engine
   - 2-5 words max (e.g. "server rack architecture diagram", "python async await logo")
5. Choose filenames that are short slugs (kebab-case, no extension), e.g.
   "attention-qkv-diagram".
6. Do NOT add more than 3 images.

Return JSON matching the GlobalImagePlan schema exactly.
"""

IMAGE_PLANNER_USER_TEMPLATE = """BLOG TITLE: {blog_title}
AUDIENCE: {audience}

FULL BLOG MARKDOWN:
{merged_blog}

Return the GlobalImagePlan JSON.
"""
