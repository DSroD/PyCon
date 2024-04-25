"""SQLite utility functions"""
from sqlite3 import Cursor

from pydantic import BaseModel


def model_mapper(model: type[BaseModel]):
    """
    Returns row mapper for given model.
    """
    def mapper(cursor: Cursor, row: tuple) -> model:
        result = {}
        for idx, col in enumerate(cursor.description):
            result[col[0]] = row[idx]
        return model(**result)
    return mapper
