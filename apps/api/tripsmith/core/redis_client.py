from __future__ import annotations

import os

from redis import Redis

from tripsmith.core.config import settings


def get_redis() -> Redis:
    if os.getenv("FAKE_REDIS", "0") == "1":
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True)
    return Redis.from_url(settings.redis_url, decode_responses=True)

