import asyncio
import random
from typing import Coroutine, Optional, Callable


async def retry_jitter_exponential_backoff(
        coro: Callable[[], Coroutine],
        exc_types: tuple[type[Exception], ...],
        backoff_ms: int,
        jitter_ms: Optional[int] = None,
        max_backoff_ms: Optional[int] = None,
        max_tries: Optional[int] = None,
        on_failure: Optional[Callable[[], Coroutine]] = None,
):
    try_num = 0
    while True:
        try_num += 1
        try:
            await coro()
            break
        except exc_types:
            if max_tries and try_num >= max_tries:
                raise
            exp_ms = backoff_ms * 2 ** try_num
            add_ms = random.randint(-jitter_ms, jitter_ms) if jitter_ms else 0
            delay_seconds = max(backoff_ms, min(exp_ms + add_ms, max_backoff_ms)) / 1000
            if on_failure:
                await on_failure()
            await asyncio.sleep(delay_seconds)
            continue
        except Exception as e:
            print(e)
            raise
