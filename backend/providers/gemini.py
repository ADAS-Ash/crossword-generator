import json
import logging
import re
import time
from google import genai
from google.genai import errors, types
from .base import BaseProvider, GenerateResult
from .errors import call_with_retry, request_id_var
from backend.config import settings
from backend.models import WordClue

PROMPT_TEMPLATE = """Generate exactly {count} words and crossword-style clues about the topic: "{topic}".

Rules:
- Words must be single words (no spaces or hyphens), 3 to {max_length} letters long
- Use only uppercase A-Z letters
- Clues should be concise (under 80 characters), in standard crossword style
- Do not repeat words
- Return ONLY a JSON array: [{{"word": "EXAMPLE", "clue": "A sample instance"}}]"""

GROUNDED_PROMPT_TEMPLATE = """You have access to Google Search. Use it to find accurate, up-to-date information about: "{topic}"

Based ONLY on verified facts from your search results, generate exactly {count} words and crossword-style clues.

Rules:
- Words must be single words (no spaces or hyphens), 3 to {max_length} letters long
- Use only uppercase A-Z letters (for names like O'Brien, use OBRIEN)
- Clues should be concise (under 80 characters), in standard crossword style
- Only include facts you can verify from search results — do NOT guess or hallucinate
- Do not repeat words
- Return ONLY a JSON array: [{{"word": "EXAMPLE", "clue": "A sample instance"}}]"""

GROUNDING_KEYWORDS = [
    "2024", "2025", "2026", "2027",
    "current", "latest", "recent", "today",
    "this year", "this season", "this summer", "this winter",
    "transfer", "signed", "elected", "announced",
    "new release", "just released", "premiered",
    "who won", "who is",
]


logger = logging.getLogger("crossword.llm")

# Monotonic time until which Google Search grounding is skipped after a quota error.
_search_disabled_until = 0.0


def _needs_grounding(topic: str) -> bool:
    topic_lower = topic.lower()
    return any(kw in topic_lower for kw in GROUNDING_KEYWORDS)


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        self.client = genai.Client(api_key=api_key)

    async def generate_words(self, topic: str, count: int, max_length: int) -> GenerateResult:
        use_grounding = _needs_grounding(topic)
        if use_grounding and _search_paused():
            logger.info(
                "search skipped rid=%s reason=quota_cooldown remaining_s=%d",
                request_id_var.get(), int(_search_disabled_until - time.monotonic()),
            )
            use_grounding = False

        grounded_prompt = GROUNDED_PROMPT_TEMPLATE.format(
            topic=topic, count=count, max_length=max_length,
        )
        grounded_config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )
        plain_prompt = PROMPT_TEMPLATE.format(
            topic=topic, count=count, max_length=max_length,
        )
        plain_config = types.GenerateContentConfig(response_mime_type="application/json")

        models = _model_schedule(
            settings.gemini_model, settings.gemini_fallback_models, settings.llm_max_attempts,
        )

        async def attempt(model: str, _attempt: int) -> GenerateResult:
            if use_grounding and not _search_paused():
                try:
                    response = await self.client.aio.models.generate_content(
                        model=model,
                        contents=grounded_prompt,
                        config=grounded_config,
                    )
                    return _parse_response(response, count, max_length, grounded=True)
                except errors.APIError as e:
                    if e.code != 429:
                        raise
                    # Search quota is per key, so other models won't help; generate
                    # without search and stop trying it for a while.
                    _pause_search(model, e)

            response = await self.client.aio.models.generate_content(
                model=model,
                contents=plain_prompt,
                config=plain_config,
            )
            return _parse_response(response, count, max_length, grounded=False)

        return await call_with_retry(
            attempt,
            provider="gemini",
            models=models,
            max_attempts=settings.llm_max_attempts,
            base_delay=settings.llm_retry_base_delay,
            timeout=settings.llm_timeout_seconds,
        )


def _search_paused() -> bool:
    return time.monotonic() < _search_disabled_until


def _pause_search(model: str, exc: errors.APIError) -> None:
    global _search_disabled_until
    _search_disabled_until = time.monotonic() + settings.gemini_search_cooldown_seconds
    logger.warning(
        "search quota exhausted rid=%s model=%s status=%s; generating without search "
        "and skipping search for %ds msg=%r",
        request_id_var.get(), model, exc.code,
        settings.gemini_search_cooldown_seconds, (exc.message or "")[:200],
    )


def _model_schedule(primary: str, fallbacks: str, attempts: int) -> list[str]:
    """Model to use for each attempt: the primary first, then each fallback in order.

    If there are more attempts than models, the primary is retried before falling back;
    if there are fewer, later fallbacks are dropped.
    e.g. 3 attempts + 2 fallbacks -> [primary, fb1, fb2]
         4 attempts + 1 fallback  -> [primary, primary, primary, fb1]
    """
    chain = [m.strip() for m in fallbacks.split(",") if m.strip() and m.strip() != primary]
    chain = chain[: max(attempts - 1, 0)]
    return [primary] * (attempts - len(chain)) + chain


def _parse_response(response, count: int, max_length: int, grounded: bool) -> GenerateResult:
    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        prompt_tokens = getattr(um, "prompt_token_count", None)
        completion_tokens = getattr(um, "candidates_token_count", None)
        if prompt_tokens and completion_tokens:
            total_tokens = prompt_tokens + completion_tokens

    if not response.text:
        finish = None
        if response.candidates:
            finish = getattr(response.candidates[0], "finish_reason", None)
        raise ValueError(f"Empty response from model (finish_reason={finish})")

    text = response.text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group()

    try:
        pairs = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON ({e}): {text[:200]!r}") from e

    results = []
    for p in pairs:
        word = p.get("word", "").upper().strip()
        clue = p.get("clue", "").strip()
        if word.isalpha() and 3 <= len(word) <= max_length and clue:
            results.append(WordClue(word=word, clue=clue))

    if not results:
        raise ValueError(f"Model returned no usable words: {text[:200]!r}")

    return GenerateResult(
        words=results[:count],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        grounded=grounded,
    )
