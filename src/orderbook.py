import binascii
import pandas as pds
from sqlalchemy import Table, Column, MetaData, BigInteger, LargeBinary, engine

from src.db.pg_client import pg_engine


def bin_str(bin: memoryview) -> str:
    return "0x" + bin.hex()


def pandas_query(db: engine):
    print("Pandas")
    df = pds.read_sql("select * from invalidations", db)
    for uid in df.order_uid:
        print(bin_str(uid))


def sql_alchemy(db: engine):
    print("SQL Alchemy")
    meta = MetaData(db)
    invalidation_table = Table(
        "invalidations",
        meta,
        Column("block_number", BigInteger),
        Column("log_index", BigInteger),
        Column("order_uid", LargeBinary),
    )

    with db.connect() as conn:

        select_statement = invalidation_table.select()
        result_set = conn.execute(select_statement)
        for r in result_set:
            print(bin_str(r.order_uid))


if __name__ == "__main__":
    db_engine = pg_engine()
    sql_alchemy(db_engine)
    pandas_query(db_engine)
