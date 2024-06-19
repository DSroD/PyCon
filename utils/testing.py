"""General utility functions and classes for tests."""
import asyncio
from datetime import datetime, tzinfo, timedelta


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


class PacketProvider:
    """Provides packets"""
    def __init__(self, packets: bytes):
        self._packets = packets

    def __call__(self, n: int):
        return self._get(n)

    async def _get(self, n: int):
        if n > len(self._packets):
            raise asyncio.IncompleteReadError(self._packets, n)
        res = self._packets[:n]
        self._packets = self._packets[n:]
        return res
