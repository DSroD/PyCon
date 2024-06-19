"""Migration code for sqlite db."""
import itertools
import json
import logging
import sqlite3
from datetime import datetime
from sqlite3 import Connection

# TODO: This should be refactored as it is just quickly hacked together.

logger = logging.getLogger(__name__)


def migrate(
        db: str | Connection,
        migrations_file="migrations.json",
        close=True
):
    """Performs sqlite db migrations from json file"""
    con = sqlite3.connect(db) if isinstance(db, str) else db
    with con:
        _create_if_not_exists(con)

    applied = _get_migrations(con)
    with open(migrations_file, "r", encoding='utf-8') as mig_file:
        migs = json.load(mig_file)
        for mig_name, mig_op in migs.items():
            if mig_name in applied:
                continue
            _apply_mig(con, mig_name, mig_op)
            logger.info("Performed migration %s", mig_name)
    if close:
        con.close()


def _create_if_not_exists(con: Connection):
    con.execute("CREATE TABLE IF NOT EXISTS migrations(name VARCHAR PRIMARY KEY, executed_at TEXT)")


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
    cols: dict[str, str | dict] = op["columns"]
    for col_name, col_data in cols.items():
        if isinstance(col_data, str):
            yield f"{col_name} {col_data.upper()}"
        else:
            col_type = col_data["type"]
            nullable = col_data["nullable"] if "nullable" in col_data else True
            nullable_str = "" if nullable else " NOT NULL"
            default_str = f" DEFAULT {col_data['default']}" if "default" in col_data else ""
            yield f"{col_name} {col_type.upper()}{nullable_str}{default_str}"


def _pk_gen(op: dict):
    pk: list[str] | str = op["pk"]
    if isinstance(pk, str):
        yield f"PRIMARY KEY ({pk})"
    else:
        yield f"PRIMARY KEY({','.join(pk)})"


def _fk_gen(op: dict):
    fks: dict[str, dict[str, str]] = op["fk"] if "fk" in op else {}
    for col, fk in fks.items():
        yield f"FOREIGN KEY({col}) REFERENCES {fk['table']}({fk['column']})"


def _unique_gen(op: dict):
    uniques: list[list[str] | str] = op["unique"] if "unique" in op else []
    for unique in uniques:
        if isinstance(unique, str):
            yield f"UNIQUE({unique})"
        else:
            yield f"UNIQUE({','.join(unique)})"


def _create_table(con: Connection, op: dict):
    table_name = op["table_name"]

    bracket = ",".join(
        itertools.chain(
            _cols_gen(op),
            _pk_gen(op),
            _fk_gen(op),
            _unique_gen(op),
        )
    )

    sql = f"CREATE TABLE {table_name}({bracket})"
    con.execute(sql)


def _apply_mig(con: Connection, mig_name: str, mig_op: dict):
    with con:
        mig_type = mig_op["type"]
        if mig_type == 'create_table':
            _create_table(con, mig_op)
        else:
            raise ValueError("Unknown migration type.")
        _insert_executed_migration(con, mig_name)
