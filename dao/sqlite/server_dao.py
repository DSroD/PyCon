import sqlite3
import uuid
from typing import Optional, List

from dao.server_dao import ServerDao
from models.server import Server


class ServerDaoImpl(ServerDao):

    def __init__(self, db_name):
        self._table_name = 'servers'
        self._db_name = db_name

    async def initialize(self):
        pass

    def _conn(self):
        return sqlite3.connect(self._db_name)

    async def get_all(self) -> List[Server]:
        pass

    async def get_user_servers(self, username: str) -> List[Server]:
        pass

    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        pass
