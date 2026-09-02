from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    grid_size: int = Field(default=15, ge=8, le=25)
    word_count: int = Field(default=20, ge=5, le=40)


class WordClue(BaseModel):
    word: str
    clue: str


class WordEntry(BaseModel):
    word: str
    clue: str
    row: int
    col: int
    direction: str
    number: int
    length: int


class PuzzleMetadata(BaseModel):
    topic: str
    grid_size: int
    words_placed: int
    words_requested: int
    provider: str
    grounded: bool = False


class GenerateResponse(BaseModel):
    grid: list[list[str]]
    words: list[WordEntry]
    metadata: PuzzleMetadata
    puzzle_id: str | None = None
