"""General utility functions for tests."""
import asyncio


async def yield_to_event_loop():
    """Yields control to the event loop."""
    # This approach was discussed in https://github.com/python/asyncio/issues/284
    await asyncio.sleep(0)
