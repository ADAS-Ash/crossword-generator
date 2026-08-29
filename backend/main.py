from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models import GenerateRequest, GenerateResponse, WordEntry, PuzzleMetadata
from backend.generator import CrosswordGenerator
from backend.providers import get_provider

app = FastAPI(title="Crossword Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "provider": settings.llm_provider}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_crossword(request: GenerateRequest):
    provider = get_provider()

    try:
        word_clues = await provider.generate_words(
            topic=request.topic,
            count=request.word_count,
            max_length=request.grid_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM provider error: {e}")

    if not word_clues:
        raise HTTPException(status_code=500, detail="No words generated")

    clue_lookup = {wc.word: wc.clue for wc in word_clues}

    gen = CrosswordGenerator(size=request.grid_size)
    gen.generate(list(clue_lookup.keys()))
    gen.crop()

    cell_numbers = gen.number_clues()
    grid = gen.build_response_grid()

    words = []
    for pw in gen.placed_words:
        num = cell_numbers.get((pw["row"], pw["col"]), 0)
        direction = "across" if pw["direction"] == "H" else "down"
        words.append(WordEntry(
            word=pw["word"],
            clue=clue_lookup.get(pw["word"], ""),
            row=pw["row"],
            col=pw["col"],
            direction=direction,
            number=num,
            length=len(pw["word"]),
        ))

    words.sort(key=lambda w: (w.direction, w.number))

    return GenerateResponse(
        grid=grid,
        words=words,
        metadata=PuzzleMetadata(
            topic=request.topic,
            grid_size=request.grid_size,
            words_placed=len(gen.placed_words),
            words_requested=request.word_count,
            provider=settings.llm_provider,
        ),
    )
