"""Server models."""
import uuid
from enum import Enum
from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field


class Server(BaseModel):
    """Server model."""
    class Type(Enum):
        """Server type."""
        SOURCE_SERVER = 1
        MINECRAFT_SERVER = 2

    type: Type
    name: str
    description: str = ""
    host: str
    port: int
    rcon_port: int
    rcon_password: str
    uid: uuid.UUID = Field(default_factory=uuid.uuid4)


# pylint: disable-next=too-many-arguments
def from_form_data(
        uid: Annotated[str, Form(default_factory=uuid.uuid4)],
        server_type: Annotated[str, Form()],
        name: Annotated[str, Form()],
        description: Annotated[str, Form()],
        host: Annotated[str, Form()],
        port: Annotated[int, Form()],
        rcon_port: Annotated[int, Form()],
        rcon_password: Annotated[str, Form()],
):
    """Returns server model from Form data."""
    return Server(
        uid=uid,
        type=Server.Type[server_type],
        name=name,
        description=description,
        host=host,
        port=port,
        rcon_port=rcon_port,
        rcon_password=rcon_password,
    )
