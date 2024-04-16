from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable


class PubSubFilter[TMessage](ABC):
    @abstractmethod
    def accept(self, message: TMessage) -> bool:
        pass

    def __and__(self, other: PubSubFilter):
        return _FilterAnd(self, other)

    def __or__(self, other: PubSubFilter):
        return _FilterOr(self, other)

    def __invert__(self):
        return _FilterNot(self)


class _FilterNot[TMessage](PubSubFilter[TMessage]):
    def __init__(self, inner: PubSubFilter):
        self._inner = inner

    def accept(self, message: TMessage) -> bool:
        return not self._inner.accept(message)


class _FilterAnd[TMessage](PubSubFilter[TMessage]):
    def __init__(self, left: PubSubFilter[TMessage], right: PubSubFilter[TMessage]):
        self._left = left
        self._right = right

    def accept(self, message: TMessage) -> bool:
        return self._left.accept(message) and self._right.accept(message)


class _FilterOr[TMessage](PubSubFilter[TMessage]):
    def __init__(self, left: PubSubFilter[TMessage], right: PubSubFilter[TMessage]):
        self._left = left
        self._right = right

    def accept(self, message: TMessage) -> bool:
        return self._left.accept(message) or self._right.accept(message)


class FieldEquals[TMessage, TValue](PubSubFilter[TMessage]):

    def __init__(self, selector: Callable[[TMessage], TValue], value: TValue):
        self._selector = selector
        self._value = value

    def accept(self, message: TMessage) -> bool:
        return self._selector(message) == self._value


class IsType[TMessage](PubSubFilter[TMessage]):
    def __init__(self, subtype: type[TMessage]):
        self._subtype = subtype

    def accept(self, message: TMessage) -> bool:
        return isinstance(message, self._subtype)


class FieldLength[TMessage, TField](PubSubFilter[TMessage]):
    class Mode(Enum):
        EQ = 0,
        MIN = 1,
        MAX = 2,

    def __init__(self, selector: Callable[[TMessage], TField], length: int, mode: FieldLength.Mode = Mode.EQ):
        self._selector = selector
        self._length = length
        self._mode = mode

    def accept(self, message: TMessage) -> bool:
        field = self._selector(message)
        length = len(field)
        if self._mode == self.Mode.EQ:
            return length == self._length
        if self._mode == self.Mode.MIN:
            return length >= self._length
        if self._mode == self.Mode.MAX:
            return length <= self._length
        return False


class FieldContains[TMessage, TValue, TField: list](PubSubFilter[TMessage]):
    def __init__(self, selector: Callable[[TMessage], TField], value: TValue):
        self._selector = selector
        self._value = value

    def accept(self, message: TMessage) -> bool:
        field = self._selector(message)
        return self._value in field
