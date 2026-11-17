
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy.engine import make_url

from ..api.database import DATABASE_URL


database_url = make_url(DATABASE_URL)

if database_url.drivername.startswith("postgresql+"):
    database_url = database_url.set(drivername="postgresql")

POSTGRES_DSN = database_url.render_as_string(hide_password=False)


connection_pool = ConnectionPool(
    conninfo=POSTGRES_DSN,
    min_size=1,
    max_size=10,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
    },
    open=False,
)

postgres_checkpointer = None


def iniciar_checkpointer():
    global postgres_checkpointer

    if postgres_checkpointer is not None:
        return postgres_checkpointer

    connection_pool.open(wait=True)

    postgres_checkpointer = PostgresSaver(connection_pool)
    postgres_checkpointer.setup()

    return postgres_checkpointer


def fechar_checkpointer():
    global postgres_checkpointer

    if postgres_checkpointer is not None:
        connection_pool.close()
        postgres_checkpointer = None
