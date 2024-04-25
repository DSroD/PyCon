"""Migration code for sqlite db"""
import itertools
import json
import sqlite3
from datetime import datetime
from sqlite3 import Connection
from typing import Optional


def _create_if_not_exists(con: Connection):
    con.execute("CREATE TABLE IF NOT EXISTS migrations(name VARCHAR PRIMARY KEY, executed_at TEXT)")


def _get_latest_migration(con: Connection) -> Optional[str]:
    cur = con.execute("SELECT name FROM migrations ORDER BY executed_at DESC LIMIT 1")
    result = cur.fetchone()
    if result:
        return result[0]
    return None


def _get_migrations(con: Connection) -> list[str]:
    cur = con.execute("SELECT name FROM migrations")
    result = cur.fetchall()
    return list(map(lambda tup: tup[0], result))


def _insert_executed_migration(con: Connection, mig_name: str):
    now = datetime.now().isoformat()
    con.execute(
        "INSERT INTO migrations VALUES (?, ?)",
        (mig_name, now)
    )


def _cols_gen(op: dict):
    cols: dict[str, str] = op["columns"]
    for col_name, col_type in cols.items():
        yield f"{col_name} {col_type.upper()}"


def _pk_gen(op: dict):
    pk: list[str] = op["pk"]
    yield f"PRIMARY KEY({','.join(pk)})"


def _fk_gen(op: dict):
    fks: dict[str, dict[str, str]] = op["fk"] if "fk" in op else {}
    for col, fk in fks.items():
        yield f"FOREIGN KEY({col}) REFERENCES {fk['table']}({fk['column']})"


def _create_table(con: Connection, op: dict):
    table_name = op["table_name"]

    bracket = ",".join(
        itertools.chain(
            _cols_gen(op),
            _pk_gen(op),
            _fk_gen(op)
        )
    )

    sql = f"CREATE TABLE {table_name}({bracket})"
    con.execute(sql)


def _apply_mig(con: Connection, mig_name: str, mig_op: dict):
    mig_type = mig_op["type"]
    if mig_type == 'create_table':
        _create_table(con, mig_op)
    else:
        raise LookupError("Unknown migration type.")  # TODO: better exception
    _insert_executed_migration(con, mig_name)


def migrate(
        db_name: str
):
    """Performs sqlite db migrations from migrations.json file"""
    with sqlite3.connect(db_name) as con:
        _create_if_not_exists(con)

        applied = _get_migrations(con)
        with open("migrations.json", "r", encoding='utf-8') as mig_file:
            migs = json.load(mig_file)
            for mig_name, mig_op in migs.items():
                if mig_name in applied:
                    continue
                _apply_mig(con, mig_name, mig_op)


migrate("pycon.sqlite3")
