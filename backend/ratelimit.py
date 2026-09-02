import time
from collections import defaultdict

from backend.config import settings


class RateLimiter:
    def __init__(self):
        self._requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        limit = settings.rate_limit_per_day
        if limit <= 0:
            return True

        now = time.time()
        cutoff = now - 86400
        timestamps = self._requests[client_ip]
        self._requests[client_ip] = [t for t in timestamps if t > cutoff]

        if len(self._requests[client_ip]) >= limit:
            return False

        self._requests[client_ip].append(now)
        return True

    def remaining(self, client_ip: str) -> int:
        limit = settings.rate_limit_per_day
        if limit <= 0:
            return 999

        now = time.time()
        cutoff = now - 86400
        timestamps = self._requests[client_ip]
        recent = [t for t in timestamps if t > cutoff]
        return max(0, limit - len(recent))


rate_limiter = RateLimiter()
