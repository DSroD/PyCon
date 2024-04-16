import uuid
from enum import Enum

from pydantic import BaseModel, Field


class Server(BaseModel):
    class Type(Enum):
        SOURCE_SERVER = 1,
        MINECRAFT_SERVER = 2,

    type: Type
    name: str
    host: str
    port: int
    rcon_port: int
    rcon_password: str
    description: str = ""
    uid: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
