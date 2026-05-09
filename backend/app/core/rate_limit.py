from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = monotonic()
        hits = self._hits[key]
        while hits and hits[0] <= now - window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
            )
        hits.append(now)


rate_limiter = MemoryRateLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request, scope: str, limit: int = 30, window_seconds: int = 60) -> None:
    rate_limiter.check(f"{scope}:{client_ip(request)}", limit, window_seconds)
