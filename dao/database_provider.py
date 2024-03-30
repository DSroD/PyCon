from enum import Enum


class DatabaseProvider(Enum):
    IN_MEMORY = "IN_MEMORY",
    SQLITE = "SQLITE",
