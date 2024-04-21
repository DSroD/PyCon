"""Providers of request IDs."""


class IntRequestIdProvider:
    """Provides IDs to use in a request."""
    def __init__(self):
        self._counter = -2147483648

    def get_request_id(self) -> int:
        """Returns next request ID."""
        self._counter += 1
        return self._counter
