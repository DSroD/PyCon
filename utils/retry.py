"""Provides logic for retrying operations."""
import asyncio
import random
from dataclasses import dataclass
from typing import Coroutine, Optional, Callable


@dataclass(eq=True, frozen=True)
class RetryConfiguration:
    """Configuration for retryable operations with exponential backoff."""
    backoff_ms: int
    jitter_ms: Optional[int] = None
    max_backoff_ms: Optional[int] = None
    max_tries: Optional[int] = None


async def retry_jitter_exponential_backoff(
        coro: Callable[[], Coroutine],
        exc_types: tuple[type[Exception], ...],
        retry_configuration: RetryConfiguration,
        on_failure: Optional[Callable[[], Coroutine]] = None,
):
    """
    Retry a coroutine with exponential backoff.

    :param coro: Coroutine supplier
    :param exc_types: Exception types to retry on
    :param retry_configuration: Configuration of retrying
    :param on_failure: Supplier of coroutine to call on exception from exc_types
    :return: Retryable coroutine
    """
    try_num = 0
    while True:
        try_num += 1
        try:
            await coro()
            break
        except exc_types:
            if retry_configuration.max_tries and try_num >= retry_configuration.max_tries:
                raise
            exp_ms = retry_configuration.backoff_ms * 2 ** try_num
            # pylint: disable-next=invalid-unary-operand-type
            add_ms = random.randint(
                -retry_configuration.jitter_ms,
                retry_configuration.jitter_ms
            ) if retry_configuration.jitter_ms else 0
            delay_seconds = max(
                retry_configuration.backoff_ms, min(
                    exp_ms + add_ms, retry_configuration.max_backoff_ms
                )
            ) / 1000
            if on_failure:
                await on_failure()
            await asyncio.sleep(delay_seconds)
            continue
