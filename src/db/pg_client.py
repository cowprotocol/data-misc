import os

import psycopg2
from dotenv import load_dotenv
from psycopg2._psycopg import connection
from sqlalchemy import create_engine, Engine

load_dotenv()
host = os.environ["ORDERBOOK_HOST"]
port = os.environ["ORDERBOOK_PORT"]
database = os.environ["ORDERBOOK_DB"]
user = os.environ["ORDERBOOK_USER"]
password = os.environ["ORDERBOOK_PASSWORD"]


def pg_connect() -> connection:
    """
    warnings.warn(
        "pandas only support SQLAlchemy connectable(engine/connection) or"
        "database string URI or sqlite3 DBAPI2 connection"
        "other DBAPI2 objects are not tested, please consider using SQLAlchemy",
        UserWarning,
    )
    """
    return psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )


def pg_engine() -> Engine:
    return create_engine(db_string())


def db_string() -> str:
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
