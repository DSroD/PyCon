
class RequestIdProvider:
    def __init__(self):
        self._counter = -2147483648

    def get_request_id(self) -> int:
        self._counter += 1
        return self._counter
