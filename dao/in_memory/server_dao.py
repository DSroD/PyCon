import uuid
from typing import List, Optional

from dao.server_dao import ServerDao
from models.server import Server


class ServerDaoImpl(ServerDao):
    def __init__(self):
        self._servers = {
            uuid.UUID("141a5347-abfc-4c13-8d10-bba20a261f69"): {
                "type": Server.Type.MINECRAFT_SERVER,
                "name": "Test server",
                "host": "localhost",
                "port": 25565,
                "rcon_port": 25575,
                "rcon_password": "test_server_rcon_pwd",
                "description": "Test server description",
                "uid": uuid.UUID("141a5347-abfc-4c13-8d10-bba20a261f69"),
                "allowed_users": ["test"]
            },
            uuid.UUID("141a5347-abfc-4c13-8d10-bba20a251f69"): {
                "type": Server.Type.MINECRAFT_SERVER,
                "name": "Test server 2",
                "host": "localhost",
                "port": 25566,
                "rcon_port": 25576,
                "rcon_password": "test_server_rcon_pwd2",
                "description": "Test server 2 description",
                "uid": uuid.UUID("141a5347-abfc-4c13-8d10-bba20a251f69"),
                "allowed_users": ["test", "test2"]
            }
        }

    async def initialize(self):
        pass

    async def get_user_servers(self, username: str) -> List[Server]:
        return [Server(**server) for server in self._servers.values() if username in server["allowed_users"]]

    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        if uid in self._servers:
            return Server(**self._servers[uid])
        return None

    async def get_all(self) -> List[Server]:
        return list(map(lambda s: Server(**s), self._servers.values()))
