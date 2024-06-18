"""Helpers for async stuff"""
from asyncio import sleep


async def yield_to_event_loop():
    """Yields control to the event loop."""
    # This approach was discussed in https://github.com/python/asyncio/issues/284
    await sleep(0)
