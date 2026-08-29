import json
import re
from google import genai
from .base import BaseProvider, GenerateResult
from backend.models import WordClue

PROMPT_TEMPLATE = """Generate exactly {count} words and crossword-style clues about the topic: "{topic}".

Rules:
- Words must be single words (no spaces or hyphens), 3 to {max_length} letters long
- Use only uppercase A-Z letters
- Clues should be concise (under 80 characters), in standard crossword style
- Do not repeat words
- Return ONLY a JSON array: [{{"word": "EXAMPLE", "clue": "A sample instance"}}]"""


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        self.client = genai.Client(api_key=api_key)

    async def generate_words(self, topic: str, count: int, max_length: int) -> GenerateResult:
        prompt = PROMPT_TEMPLATE.format(topic=topic, count=count, max_length=max_length)

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            prompt_tokens = getattr(um, "prompt_token_count", None)
            completion_tokens = getattr(um, "candidates_token_count", None)
            if prompt_tokens and completion_tokens:
                total_tokens = prompt_tokens + completion_tokens

        text = response.text.strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            text = match.group()

        pairs = json.loads(text)
        results = []
        for p in pairs:
            word = p.get("word", "").upper().strip()
            clue = p.get("clue", "").strip()
            if word.isalpha() and 3 <= len(word) <= max_length and clue:
                results.append(WordClue(word=word, clue=clue))

        return GenerateResult(
            words=results[:count],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
