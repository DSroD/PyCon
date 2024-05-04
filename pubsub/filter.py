"""PubSub message filtering."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Container, override, Collection


class PubSubFilter[MessageT](ABC):
    """Filters PubSub messages."""
    @abstractmethod
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes the filter."""

    def __and__(self, other: PubSubFilter):
        return _FilterAnd(self, other)

    def __or__(self, other: PubSubFilter):
        return _FilterOr(self, other)

    def __invert__(self):
        return _FilterNot(self)


class _FilterNot[MessageT](PubSubFilter[MessageT]):
    def __init__(self, inner: PubSubFilter):
        self._inner = inner

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message did not pass the inner filter."""
        return not self._inner.accept(message)


class _FilterAnd[MessageT](PubSubFilter[MessageT]):
    def __init__(self, left: PubSubFilter[MessageT], right: PubSubFilter[MessageT]):
        self._left = left
        self._right = right

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes both filters."""
        return self._left.accept(message) and self._right.accept(message)


class _FilterOr[MessageT](PubSubFilter[MessageT]):
    def __init__(self, left: PubSubFilter[MessageT], right: PubSubFilter[MessageT]):
        self._left = left
        self._right = right

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes one of the filters."""
        return self._left.accept(message) or self._right.accept(message)


class FieldEquals[MessageT, ValueT](PubSubFilter[MessageT]):
    """Filters messages based on equality check on a value of a field."""

    def __init__(self, selector: Callable[[MessageT], ValueT], value: ValueT):
        self._selector = selector
        self._value = value

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes the FieldEquals filter."""
        return self._selector(message) == self._value


class IsType[MessageT](PubSubFilter[MessageT]):
    """Filters messages based on a type."""
    def __init__(self, subtype: type[MessageT]):
        self._subtype = subtype

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes the IsType filter."""
        return isinstance(message, self._subtype)


class FieldLength[MessageT, FieldT: Collection](PubSubFilter[MessageT]):
    """Filters messages based on a length of given field."""
    class Mode(Enum):
        """
        Comparison mode.

        EQ for equality, MIN for minimal size, MAX for maximal size.
        """
        EQ = 0
        MIN = 1
        MAX = 2

    def __init__(
            self,
            selector: Callable[[MessageT], FieldT],
            length: int,
            mode: FieldLength.Mode = Mode.EQ
    ):
        self._selector = selector
        self._length = length
        self._mode = mode

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes the FieldLength filter."""
        field = self._selector(message)
        length = len(field)
        if self._mode == self.Mode.EQ:
            return length == self._length
        if self._mode == self.Mode.MIN:
            return length >= self._length
        if self._mode == self.Mode.MAX:
            return length <= self._length
        return False


class FieldContains[MessageT, ValueT, FieldT: Container](PubSubFilter[MessageT]):
    """Filters message on value being contained in the field (using in operator)."""
    def __init__(self, selector: Callable[[MessageT], FieldT], value: ValueT):
        self._selector = selector
        self._value = value

    @override
    def accept(self, message: MessageT) -> bool:
        """Signals if message passes the FieldContains filter."""
        field = self._selector(message)
        return self._value in field
