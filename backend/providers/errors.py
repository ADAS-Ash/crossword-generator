import asyncio
import contextvars
import json
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger("crossword.llm")

# Set per request in main.py so provider logs can be correlated with the API response.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

T = TypeVar("T")

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504, 529}


class ProviderError(Exception):
    """An LLM call that failed after all retry attempts, with diagnostics attached."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str,
        kind: str,
        status_code: int | None,
        retryable: bool,
        attempts: int,
        elapsed_ms: int,
    ):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.model = model
        self.kind = kind
        self.status_code = status_code
        self.retryable = retryable
        self.attempts = attempts
        self.elapsed_ms = elapsed_ms

    def __str__(self) -> str:
        status = f" {self.status_code}" if self.status_code else ""
        return (
            f"[{self.provider}/{self.model}] {self.kind}{status} after "
            f"{self.attempts} attempt(s), {self.elapsed_ms}ms: {self.message}"
        )


def classify(exc: Exception) -> tuple[str, int | None, bool]:
    """Return (kind, status_code, retryable) for an exception raised by an LLM SDK."""
    # google-genai APIError exposes .code; anthropic APIStatusError exposes .status_code
    status = getattr(exc, "code", None)
    if not isinstance(status, int):
        status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        if status == 429:
            return "rate_limited", status, True
        if status in (401, 403):
            return "auth", status, False
        if status in RETRYABLE_STATUS:
            return "unavailable" if status in (503, 529) else "server_error", status, True
        return "client_error", status, False

    name = type(exc).__name__.lower()
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)) or "timeout" in name:
        return "timeout", None, True
    if isinstance(exc, (ConnectionError, OSError)) or "connection" in name:
        return "network", None, True
    if isinstance(exc, (json.JSONDecodeError, ValueError, KeyError, TypeError)):
        # Model returned malformed or empty output; a fresh sample usually fixes it.
        return "bad_output", None, True
    return "unknown", None, False


def _short(exc: Exception, limit: int = 300) -> str:
    text = getattr(exc, "message", None) or str(exc)
    text = " ".join(str(text).split())
    return text[:limit]


async def call_with_retry(
    fn: Callable[[str, int], Awaitable[T]],
    *,
    provider: str,
    models: list[str],
    max_attempts: int,
    base_delay: float,
    timeout: float,
) -> T:
    """Call fn(model, attempt) with exponential backoff, logging every attempt.

    `models` is the model to use per attempt; the last entry is reused once the list
    runs out, so ["primary", "primary", "fallback"] tries the fallback on attempt 3.
    """
    rid = request_id_var.get()
    start = time.monotonic()
    last_exc: Exception | None = None
    kind, status, retryable = "unknown", None, False
    model = models[0]

    for attempt in range(1, max_attempts + 1):
        model = models[min(attempt - 1, len(models) - 1)]
        t0 = time.monotonic()
        try:
            result = await asyncio.wait_for(fn(model, attempt), timeout=timeout)
            if hasattr(result, "attempts"):
                result.model = model
                result.attempts = attempt
            logger.info(
                "llm_call ok rid=%s provider=%s model=%s attempt=%d/%d latency_ms=%d",
                rid, provider, model, attempt, max_attempts, int((time.monotonic() - t0) * 1000),
            )
            return result
        except Exception as exc:  # noqa: BLE001 - every failure is classified below
            last_exc = exc
            kind, status, retryable = classify(exc)
            latency_ms = int((time.monotonic() - t0) * 1000)
            will_retry = retryable and attempt < max_attempts
            logger.warning(
                "llm_call fail rid=%s provider=%s model=%s attempt=%d/%d latency_ms=%d "
                "kind=%s status=%s exc=%s retry=%s msg=%r",
                rid, provider, model, attempt, max_attempts, latency_ms,
                kind, status, type(exc).__name__, will_retry, _short(exc),
            )
            if not will_retry:
                break
            # Full jitter: spreads retries out so we don't hammer an overloaded endpoint in sync.
            delay = random.uniform(0, base_delay * (2 ** (attempt - 1)))
            await asyncio.sleep(delay)

    elapsed_ms = int((time.monotonic() - start) * 1000)
    assert last_exc is not None
    raise ProviderError(
        _short(last_exc),
        provider=provider,
        model=model,
        kind=kind,
        status_code=status,
        retryable=retryable,
        attempts=attempt,
        elapsed_ms=elapsed_ms,
    ) from last_exc
