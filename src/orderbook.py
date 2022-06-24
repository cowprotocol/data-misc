import pandas as pds
from sqlalchemy import (
    Table,
    Column,
    MetaData,
    BigInteger,
    LargeBinary,
    engine,
    ForeignKey,
    PrimaryKeyConstraint,
    select,
    func,
    case,
)
from sqlalchemy.engine import LegacyCursorResult
from sqlalchemy.ext.declarative import declarative_base
from src.db.pg_client import pg_engine


Base = declarative_base()


# class Trade(Base):
#     __tablename__ = "trades"
#
#     order_uid = Column("order_uid", LargeBinary, ForeignKey("orders.uid"))
#     block_number = Column("block_number", BigInteger)
#     log_index = Column("log_index", BigInteger)
#
#     __table_args__ = (
#         PrimaryKeyConstraint(block_number, log_index),
#         {},
#     )
#
#
# class Order(Base):
#     __tablename__ = "orders"
#
#     uid = Column("uid", LargeBinary, primary_key=True)
#     owner = Column("owner", BigInteger)


def bin_str(bin: memoryview) -> str:
    return "0x" + bin.hex()


def pandas_query(db: engine):
    print("Pandas")
    df = pds.read_sql("select * from invalidations", db)
    for uid in df.order_uid:
        print(bin_str(uid))


def sql_alchemy_basic(db: engine):
    print("Basic: SQL Alchemy")
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
        result_set: LegacyCursorResult = conn.execute(select_statement)
        for r in result_set:
            print(bin_str(r.order_uid))


def sql_alchemy_advanced(db: engine):

    meta = MetaData(db)
    trades = Table(
        "trades",
        meta,
        Column("order_uid", LargeBinary),
        Column("block_number", BigInteger),
        # Could probably add all columns here, but I only need these two.
    )

    orders = Table(
        "orders",
        meta,
        Column("uid", LargeBinary),
        Column("owner", BigInteger),
    )

    join = orders.outerjoin(trades, orders.c.uid == trades.c.order_uid)
    failed_case = case(
        [(trades.c.block_number == None, 1), (trades.c.block_number != None, 0)]
    )
    success_case = case(
        [(trades.c.block_number == None, 0), (trades.c.block_number != None, 1)]
    )
    successes = func.sum(success_case)
    failures = func.sum(failed_case)
    select_statement = (
        select(
            [
                orders.c.owner,
                failures.label("failed"),
                successes.label("success"),
            ]
        )
        .select_from(join)
        .group_by(orders.c.owner)
        .having(func.sum(success_case) > 20)
        .having(func.sum(failed_case) > func.sum(success_case))
        .order_by(successes.desc())
    )
    with db.connect() as conn:
        print("Querying for spam traders having more failed orders than successful")
        result_set: LegacyCursorResult = conn.execute(select_statement)
        results = result_set.all()
        print(f"Found {len(results)} traders with more failed orders than trades")
        print(list(result_set.keys()))
        worst_first = sorted(results, key=lambda r: -r.failed / r.success)
        for rec in worst_first:
            print(bin_str(rec.owner), rec.failed, rec.success, rec.failed / rec.success)


if __name__ == "__main__":
    db_engine = pg_engine()
    sql_alchemy_basic(db_engine)
    # pandas_query(db_engine)
    sql_alchemy_advanced(db_engine)
