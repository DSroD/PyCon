"""General utility functions and classes for tests."""
import asyncio
from datetime import datetime, tzinfo, timedelta


async def yield_to_event_loop():
    """Yields control to the event loop."""
    # This approach was discussed in https://github.com/python/asyncio/issues/284
    await asyncio.sleep(0)


class TestTimeProvider:
    """Time provider to be used in tests to set exact time."""
    def __init__(self, time: datetime):
        self._time = time

    def __call__(self, tzone: tzinfo):
        return self._time.astimezone(tzone)

    def set_time(self, time: datetime):
        """Sets time to be provided to given time"""
        self._time = time

    def pass_time(self, delta: timedelta):
        """Moves time by given timedelta"""
        self._time += delta
