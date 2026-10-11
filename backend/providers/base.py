from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from backend.models import WordClue


@dataclass
class GenerateResult:
    words: list[WordClue] = field(default_factory=list)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    grounded: bool = False
    model: str | None = None
    attempts: int = 1


class BaseProvider(ABC):
    @abstractmethod
    async def generate_words(self, topic: str, count: int, max_length: int) -> GenerateResult:
        ...
