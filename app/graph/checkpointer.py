from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings


def _psycopg_conn_string() -> str:
    # PostgresSaver uses psycopg directly (libpq URI syntax), not
    # SQLAlchemy's "+psycopg" driver-selection suffix.
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


@contextmanager
def get_checkpointer():
    # A single long-lived Connection (the previous approach, matching
    # PostgresSaver.from_conn_string) dies silently whenever Neon closes it
    # for being idle — confirmed live: every request after that permanently
    # 500s ("the connection is closed") until the process is restarted.
    # ConnectionPool with check=check_connection validates a connection
    # before handing it out and transparently replaces dead ones, so an
    # idle-killed connection self-heals on the next request instead.
    with ConnectionPool(
        _psycopg_conn_string(),
        min_size=1,
        max_size=5,
        check=ConnectionPool.check_connection,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    ) as pool:
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()  # idempotent
        yield checkpointer
