# type: ignore
import time

import pandas as pd
from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network
from pandas import DataFrame
from sqlalchemy import (
    Table,
    Column,
    MetaData,
    BigInteger,
    LargeBinary,
    engine,
    select,
    func,
    case,
)

from sqlalchemy.engine import CursorResult

from src.db.pg_client import pg_engine

# pylint:disable=missing-function-docstring
pd.options.display.max_colwidth = None
pd.options.display.max_columns = None


def timeit(f):
    """Simple program timer, meant to be used as a decorator"""

    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print(f"  func:{f.__name__} took: {te - ts} sec")
        return result

    return timed


def bin_str(bytea: memoryview) -> str:
    """
    String representation of binary object `memoryview` returned from pd.read_sql on bytea columns
    """
    return "0x" + bytea.hex()


def pandas_query(db: engine):
    print("Pandas: Basic")
    df = pd.read_sql("select * from invalidations", db)
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
        result_set: CursorResult = conn.execute(select_statement)
        for r in result_set:
            print(bin_str(r.order_uid))


# pylint:disable=too-many-locals
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
        [(trades.c.block_number is None, 1), (trades.c.block_number is not None, 0)]
    )
    success_case = case(
        [(trades.c.block_number is None, 0), (trades.c.block_number is not None, 1)]
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
        result_set: CursorResult = conn.execute(select_statement)
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
        result_set: CursorResult = conn.execute(raw_query)
        print(f"Found {len(result_set.all())} with raw query")


@timeit
def query_dune(dune: DuneAPI, raw_query: str) -> DataFrame:
    query = DuneQuery.from_environment(
        raw_sql=raw_query,
        name="",
        network=Network.MAINNET,
        parameters=[],
    )
    print("Querying Dune")
    results = pd.DataFrame(dune.fetch(query))
    print(f"Got {len(results)} results")
    return results


@timeit
def query_orderbook(db: engine, raw_query: str) -> DataFrame:
    print("Querying orderbook")
    results = pd.read_sql(raw_query, db)
    print(f"Got {len(results)} results")
    return results


def order_fill_time(db: engine, dune: DuneAPI):
    print("Pandas: Advanced")
    orderbook_query = """
    select encode(uid, 'hex') as uid, date_trunc('second', creation_timestamp) as creation_timestamp 
    from trades
        join orders on uid = order_uid
    -- where creation_timestamp > now() - interval '3 months'
    where is_liquidity_order = false
    and partially_fillable = false
    -- Validity < 1 hour.
    and EXTRACT(EPOCH FROM to_timestamp(valid_to)::timestamptz - creation_timestamp) < 60 * 60
    """
    creation_df = query_orderbook(db, orderbook_query)

    dune_query = """
    select encode(order_uid, 'hex') as order_uid, block_time from gnosis_protocol_v2."trades"
    -- where block_time > now() - interval '3 months'
    """
    settlement_df = query_dune(dune, dune_query)

    joined_df = pd.merge(
        creation_df, settlement_df, how="inner", left_on="uid", right_on="order_uid"
    )

    start = pd.to_datetime(joined_df.creation_timestamp)
    end = pd.to_datetime(joined_df.block_time)
    joined_df["wait_time"] = (
        end - start
    ).dt.seconds * 60  # / np.timedelta64(1, "s")  # .dt.seconds / 60
    sorted_df = joined_df.sort_values(by=["wait_time"], ascending=False)
    # Exclude negative wait times (two different clocks)
    sorted_df = sorted_df[sorted_df.wait_time > 0]
    print("Longest 10 wait times")
    print(sorted_df[["order_uid", "block_time", "wait_time"]].head(10))
    print("Shortest 10 wait times")
    print(sorted_df[["order_uid", "block_time", "wait_time"]].tail(10))
    print(sorted_df["wait_time"].describe())


if __name__ == "__main__":
    db_engine = pg_engine()
    # sql_alchemy_basic(db_engine)
    # pandas_query(db_engine)
    # sql_alchemy_advanced(db_engine)

    dune_connection = DuneAPI.new_from_environment()
    order_fill_time(db_engine, dune_connection)
