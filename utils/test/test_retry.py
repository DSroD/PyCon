"""Retry (from utils) logic tests"""
# pylint: disable=missing-class-docstring
import unittest

from utils.retry import RetryConfiguration, retry_jitter_exponential_backoff as retry


class RetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_retry_retries(self):
        """Tests retry restarts given coroutine after failure"""
        retry_config = RetryConfiguration(
            backoff_ms=1,
        )

        res = []

        provider = _ArgProvider()

        async def work(arg):
            if arg:
                res.append(1)
                return
            res.append(0)
            raise ValueError()

        await retry(
            lambda: work(provider()),
            (ValueError,),
            retry_config,
        )

        # One failure and one success of work coroutine
        self.assertEqual(res, [0, 1])

    async def test_max_retries(self):
        """Tests coroutine is retried only max_tries times."""
        retry_config = RetryConfiguration(
            backoff_ms=1,
            max_tries=4,
        )

        res = []

        async def work():
            res.append(0)
            raise ValueError

        with self.assertRaises(ValueError):

            await retry(
                work,
                (ValueError,),
                retry_config,
            )

        # 4 tries
        self.assertEqual([0, 0, 0, 0], res)

    async def test_failure_callback(self):
        """Tests if failure callback is called on every recoverable fail"""
        retry_config = RetryConfiguration(
            backoff_ms=1,
            max_tries=2,
        )

        async def work():
            raise ValueError()

        res = []

        async def failure():
            res.append(0)

        with self.assertRaises(ValueError):

            await retry(
                work,
                (ValueError,),
                retry_config,
                failure
            )

        self.assertEqual([0, 0], res)


class _ArgProvider:
    """Provides 0 on first call and 1 on second call"""
    def __init__(self):
        self.ncall = 0

    def __call__(self):
        self.ncall += 1
        if self.ncall == 1:
            return 0
        return 1
