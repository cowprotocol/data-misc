import pandas as pds
from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network
import numpy as np
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

pds.options.display.max_colwidth = None
pds.options.display.max_columns = None
# Base = declarative_base()
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


def bin_str(bytea: memoryview) -> str:
    return "0x" + bytea.hex()


def pandas_query(db: engine):
    print("Pandas: Basic")
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
    print("Advanced: SQL Alchemy")
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

    raw_query = """
        with
    pre_table as (
        select concat('0x', encode(orders.owner, 'hex')) as trader,
            sum(case when trades.block_number is null then 1 else 0 end) as num_failed,
            sum(case when trades.block_number is not null then 1 else 0 end) as num_success
        from orders
        left outer join trades
        on order_uid = uid
        group by trader
    )
    
    select * from pre_table
    where num_success > 20
    and num_failed > num_success"""

    print("Now querying with raw sql")
    with db.connect() as conn:
        result_set: LegacyCursorResult = conn.execute(raw_query)
        print(f"Found {len(result_set.all())} with raw query")


def order_fill_time(db: engine, dune=None):
    print("Pandas: Advanced")
    orderbook_query = """
    select concat('\\x', encode(uid, 'hex')) as uid, date_trunc('second', creation_timestamp) as creation_timestamp 
    from trades
        join orders on uid = order_uid
    where creation_timestamp > now() - interval '3 months'
    and is_liquidity_order = false
    and partially_fillable = false
    
    """
    creation_df = pds.read_sql(orderbook_query, db)
    dune_query = """
    select order_uid, block_time from gnosis_protocol_v2."trades"
    where block_time > now() - interval '3 months'
    """
    query = DuneQuery.from_environment(
        raw_sql=dune_query,
        name="",
        network=Network.MAINNET,
        parameters=[],
    )
    settlement_df = pds.DataFrame(DuneAPI.new_from_environment().fetch(query))

    joined_df = pds.merge(
        creation_df, settlement_df, how="inner", left_on="uid", right_on="order_uid"
    )
    # print("Creation records", len(creation_df))
    # print("Settlement records", len(settlement_df))
    # print("Joined", len(joined_df))
    # print(joined_df[["creation_timestamp", "block_time"]].head(10))

    start = pds.to_datetime(joined_df.creation_timestamp)
    end = pds.to_datetime(joined_df.block_time)
    joined_df["wait_time"] = (end - start) / np.timedelta64(1, 'm')  #.dt.seconds / 60
    # print(joined_df.columns)
    sorted_df = joined_df.sort_values(by=["wait_time"], ascending=False)
    print(
        sorted_df[["order_uid", "creation_timestamp", "block_time", "wait_time"]].head(
            10
        )
    )

    print(
        sorted_df[["order_uid", "creation_timestamp", "block_time", "wait_time"]].tail(
            10
        )
    )
    print(
        "Average Wait time (minutes):",
        sum(joined_df["wait_time"]) / len(joined_df)
    )


if __name__ == "__main__":
    db_engine = pg_engine()
    # sql_alchemy_basic(db_engine)
    # pandas_query(db_engine)
    # sql_alchemy_advanced(db_engine)
    order_fill_time(db_engine)
