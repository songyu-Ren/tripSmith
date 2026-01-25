from __future__ import annotations

import time
from dataclasses import dataclass

from redis import Redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


def check_rate_limit(
    redis: Redis,
    *,
    user_id: str,
    route: str,
    limit_per_minute: int,
) -> RateLimitResult:
    now = int(time.time())
    window = now // 60
    key = f"rl:{user_id}:{route}:{window}"
    count = int(redis.incr(key))
    if count == 1:
        redis.expire(key, 75)
    remaining = max(0, limit_per_minute - count)
    if count <= limit_per_minute:
        return RateLimitResult(True, remaining, 0)
    retry_after = 60 - (now % 60)
    return RateLimitResult(False, 0, retry_after)

