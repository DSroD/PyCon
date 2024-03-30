import uuid

from pydantic import BaseModel, Field


class Server(BaseModel):
    name: str
    host: str
    port: int
    rcon_port: int
    rcon_password: str
    description: str = ""
    uid: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
