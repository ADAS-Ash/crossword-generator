from abc import ABC, abstractmethod
from backend.models import WordClue


class BaseProvider(ABC):
    @abstractmethod
    async def generate_words(self, topic: str, count: int, max_length: int) -> list[WordClue]:
        ...
