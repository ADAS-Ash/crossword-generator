import json
import re
import anthropic
from .base import BaseProvider
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
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate_words(self, topic: str, count: int, max_length: int) -> list[WordClue]:
        prompt = PROMPT_TEMPLATE.format(topic=topic, count=count, max_length=max_length)

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
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

        return results[:count]
