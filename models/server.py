"""Server models."""
import uuid
from enum import Enum

from pydantic import BaseModel, Field


class Server(BaseModel):
    """Server model."""
    class Type(Enum):
        """Server type."""
        SOURCE_SERVER = 1
        MINECRAFT_SERVER = 2

    type: Type
    name: str
    host: str
    port: int
    rcon_port: int
    rcon_password: str
    description: str = ""
    uid: uuid.UUID = Field(default_factory=uuid.uuid4)
