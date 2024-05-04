"""SQLite utility functions"""
from enum import Enum
from sqlite3 import Cursor
from typing import Optional

from pydantic import BaseModel


def model_mapper(model: type[BaseModel], default_args: Optional[dict] = None):
    """
    Returns row mapper for given model.
    """
    def mapper(cursor: Cursor, row: tuple) -> model:
        def_args = default_args if default_args else {}
        result = {}
        for idx, col in enumerate(cursor.description):
            result[col[0]] = row[idx]
        return model(**def_args, **result)
    return mapper


def enum_mapper(enum: type[Enum]):
    """Returns row mapper that maps a single returned value on a row to an enum value."""
    def mapper(cursor: Cursor, row: tuple) -> enum:
        if len(cursor.description) != 1:
            raise ValueError("Returned row must have only one column")
        return enum(row[0])
    return mapper
