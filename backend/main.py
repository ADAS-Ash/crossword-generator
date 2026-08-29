import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.models import GenerateRequest, GenerateResponse, WordEntry, PuzzleMetadata
from backend.generator import CrosswordGenerator
from backend.providers import get_provider
from backend.analytics import log_generation, get_stats

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
    start = time.monotonic()

    try:
        result = await provider.generate_words(
            topic=request.topic,
            count=request.word_count,
            max_length=request.grid_size,
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        log_generation(
            topic=request.topic,
            grid_size=request.grid_size,
            words_requested=request.word_count,
            words_placed=0,
            provider=settings.llm_provider,
            duration_ms=duration_ms,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"LLM provider error: {e}")

    if not result.words:
        duration_ms = int((time.monotonic() - start) * 1000)
        log_generation(
            topic=request.topic,
            grid_size=request.grid_size,
            words_requested=request.word_count,
            words_placed=0,
            provider=settings.llm_provider,
            duration_ms=duration_ms,
            error="No words generated",
        )
        raise HTTPException(status_code=500, detail="No words generated")

    clue_lookup = {wc.word: wc.clue for wc in result.words}

    gen = CrosswordGenerator(size=request.grid_size)
    gen.generate(list(clue_lookup.keys()))
    gen.crop()

    duration_ms = int((time.monotonic() - start) * 1000)

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

    log_generation(
        topic=request.topic,
        grid_size=request.grid_size,
        words_requested=request.word_count,
        words_placed=len(gen.placed_words),
        provider=settings.llm_provider,
        duration_ms=duration_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
    )

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


@app.get("/api/stats")
async def stats(authorization: str | None = Header(default=None)):
    admin_key = settings.admin_key
    if not admin_key:
        raise HTTPException(status_code=403, detail="Stats not configured")
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if token != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_stats()


STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
