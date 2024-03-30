import uuid
from typing import List, Optional

from dao.server_dao import ServerDao
from models.server import Server


class ServerDaoImpl(ServerDao):
    def __init__(self):
        self._servers = {
            uuid.UUID("141a5347-abfc-4c13-8d10-bba20a261f69"): {
                "name": "Test server",
                "host": "localhost",
                "port": 25565,
                "rcon_port": 25567,
                "rcon_password": "test",
                "description": "Test server description",
                "uid": uuid.UUID("141a5347-abfc-4c13-8d10-bba20a261f69"),
            }
        }

    def initialize(self):
        pass

    def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        if uid in self._servers:
            return Server(**self._servers[uid])
        return None

    def get_all(self) -> List[Server]:
        return list(map(lambda s: Server(**s), self._servers.values()))
