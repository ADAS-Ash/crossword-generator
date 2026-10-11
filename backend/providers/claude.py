import json
import re
import anthropic
from .base import BaseProvider, GenerateResult
from .errors import call_with_retry
from backend.config import settings
from backend.models import WordClue

PROMPT_TEMPLATE = """Generate exactly {count} words and crossword-style clues about the topic: "{topic}".

Rules:
- Words must be single words (no spaces or hyphens), 3 to {max_length} letters long
- Use only uppercase A-Z letters
- Clues should be concise (under 80 characters), in standard crossword style
- Do not repeat words
- Return ONLY a JSON array: [{{"word": "EXAMPLE", "clue": "A sample instance"}}]"""


class ClaudeProvider(BaseProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude provider")
        # Retries are handled (and logged) by call_with_retry instead of the SDK.
        self.client = anthropic.AsyncAnthropic(api_key=api_key, max_retries=0)

    async def generate_words(self, topic: str, count: int, max_length: int) -> GenerateResult:
        prompt = PROMPT_TEMPLATE.format(topic=topic, count=count, max_length=max_length)

        async def attempt(model: str, _attempt: int) -> GenerateResult:
            message = await self.client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_message(message, count, max_length)

        return await call_with_retry(
            attempt,
            provider="claude",
            models=[settings.claude_model],
            max_attempts=settings.llm_max_attempts,
            base_delay=settings.llm_retry_base_delay,
            timeout=settings.llm_timeout_seconds,
        )


def _parse_message(message, count: int, max_length: int) -> GenerateResult:
    prompt_tokens = getattr(message.usage, "input_tokens", None)
    completion_tokens = getattr(message.usage, "output_tokens", None)
    total_tokens = (prompt_tokens or 0) + (completion_tokens or 0) if prompt_tokens or completion_tokens else None

    if not message.content:
        raise ValueError(f"Empty response from model (stop_reason={message.stop_reason})")

    text = message.content[0].text.strip()
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
    )
