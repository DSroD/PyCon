import asyncio
import random
from typing import Coroutine, Optional


async def retry_jitter_exponential_backoff(
        coro: Coroutine,
        exc_types: list[type],
        backoff_ms: int,
        jitter_ms: Optional[int] = None,
        max_backoff_ms: Optional[int] = None,
        max_tries: Optional[int] = None,
):
    try_num = 0
    while True:
        try_num += 1
        try:
            await coro
            break
        except exc_types:
            if max_tries and try_num >= max_tries:
                raise
            exp_ms = backoff_ms * 2 ** try_num
            add_ms = random.randint(-jitter_ms, jitter_ms) if jitter_ms else 0
            delay_seconds = max(exp_ms + add_ms, max_backoff_ms) / 1000
            await asyncio.sleep(delay_seconds)
            continue
