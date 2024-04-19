import asyncio


def run_async(coro):
    """
    Runs fn in new event loop
    https://stackoverflow.com/questions/23033939/how-to-test-python-3-4-asyncio-code
    :param coro: Coroutine to run
    """
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper
