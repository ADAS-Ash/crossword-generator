import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.models import GenerateRequest, GenerateResponse, WordEntry, PuzzleMetadata
from backend.generator import CrosswordGenerator
from backend.providers import get_provider
from backend.providers.errors import ProviderError, request_id_var
from backend.analytics import log_generation, get_stats, save_puzzle, load_puzzle
from backend.ratelimit import rate_limiter

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("crossword.api")

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
async def generate_crossword(
    request: GenerateRequest,
    req: Request,
    resp: Response,
    x_user_api_key: str | None = Header(default=None),
    x_user_provider: str | None = Header(default=None),
):
    request_id = uuid.uuid4().hex[:12]
    request_id_var.set(request_id)
    resp.headers["X-Request-ID"] = request_id

    is_byok = bool(x_user_api_key and x_user_provider)
    provider_name = x_user_provider if is_byok else settings.llm_provider
    logger.info(
        "generate start rid=%s provider=%s byok=%s topic=%r grid=%d words=%d",
        request_id, provider_name, is_byok, request.topic, request.grid_size, request.word_count,
    )

    if not is_byok:
        client_ip = req.client.host if req.client else "unknown"
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Daily puzzle limit reached. Add your own API key in Settings for unlimited puzzles, or come back tomorrow!",
            )

    try:
        if is_byok:
            provider = get_provider(name=x_user_provider, api_key=x_user_api_key)
        else:
            provider = get_provider()
    except ValueError as e:
        logger.error("generate config_error rid=%s provider=%s err=%s", request_id, provider_name, e)
        raise HTTPException(status_code=400, detail=f"{e} (request {request_id})")
    start = time.monotonic()

    def log_failure(error: str, kind: str, status_code: int | None = None,
                    model: str | None = None, attempts: int | None = None):
        log_generation(
            topic=request.topic,
            grid_size=request.grid_size,
            words_requested=request.word_count,
            words_placed=0,
            provider=provider_name,
            duration_ms=int((time.monotonic() - start) * 1000),
            error=error,
            request_id=request_id,
            model=model,
            attempts=attempts,
            error_kind=kind,
            status_code=status_code,
        )

    try:
        result = await provider.generate_words(
            topic=request.topic,
            count=request.word_count,
            max_length=request.grid_size,
        )
    except ProviderError as e:
        logger.error("generate failed rid=%s %s", request_id, e)
        log_failure(e.message, e.kind, e.status_code, e.model, e.attempts)
        # 503 tells the client "try again shortly"; 502 means the upstream rejected the request.
        http_status = 503 if e.retryable else 502
        status = f" {e.status_code}" if e.status_code else ""
        raise HTTPException(
            status_code=http_status,
            detail=(
                f"LLM provider error ({e.provider}{status} {e.kind}, "
                f"{e.attempts} attempt(s)): {e.message} [request {request_id}]"
            ),
            headers={"X-Request-ID": request_id},
        )
    except Exception as e:
        logger.exception("generate crashed rid=%s", request_id)
        log_failure(f"{type(e).__name__}: {e}", "internal")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {type(e).__name__}: {e} [request {request_id}]",
            headers={"X-Request-ID": request_id},
        )

    if not result.words:
        log_failure("No words generated", "no_words", model=result.model, attempts=result.attempts)
        raise HTTPException(
            status_code=500,
            detail=f"No words generated [request {request_id}]",
            headers={"X-Request-ID": request_id},
        )

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
        provider=provider_name,
        duration_ms=duration_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        request_id=request_id,
        model=result.model,
        attempts=result.attempts,
    )
    logger.info(
        "generate ok rid=%s provider=%s model=%s attempts=%d placed=%d/%d duration_ms=%d",
        request_id, provider_name, result.model, result.attempts,
        len(gen.placed_words), request.word_count, duration_ms,
    )

    response = GenerateResponse(
        grid=grid,
        words=words,
        metadata=PuzzleMetadata(
            topic=request.topic,
            grid_size=request.grid_size,
            words_placed=len(gen.placed_words),
            words_requested=request.word_count,
            provider=provider_name,
            grounded=result.grounded,
        ),
    )

    puzzle_id = save_puzzle(response.model_dump())
    response.puzzle_id = puzzle_id

    return response


@app.get("/api/rate-limit")
async def get_rate_limit(req: Request):
    client_ip = req.client.host if req.client else "unknown"
    return {
        "limit": settings.rate_limit_per_day,
        "remaining": rate_limiter.remaining(client_ip),
    }


@app.get("/api/puzzle/{puzzle_id}")
async def get_puzzle(puzzle_id: str):
    if len(puzzle_id) > 16 or not puzzle_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid puzzle ID")
    data = load_puzzle(puzzle_id)
    if not data:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    return data


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
