"""Basic client for connecting to postgres database with login credentials"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

import pandas as pd
from dotenv import load_dotenv
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


REORG_THRESHOLD = 65


class OrderbookEnv(Enum):
    """
    Enum for distinguishing between CoW Protocol's staging and production environment
    """

    BARN = "BARN"
    PROD = "PROD"

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class OrderbookFetcher:
    """
    A pair of Dataframes primarily intended to store query results
    from production and staging orderbook databases
    """

    @staticmethod
    def _pg_engine(db_env: OrderbookEnv) -> Engine:
        """Returns a connection to postgres database"""
        load_dotenv()
        db_url = os.environ[f"{db_env}_DB_URL"]
        db_string = f"postgresql+psycopg2://{db_url}"
        return create_engine(db_string)

    @classmethod
    def _query_both_dbs(cls, query: str) -> tuple[DataFrame, DataFrame]:
        barn = pd.read_sql(query, con=cls._pg_engine(OrderbookEnv.BARN))
        prod = pd.read_sql(query, con=cls._pg_engine(OrderbookEnv.PROD))
        return barn, prod

    @classmethod
    def get_order_creations(cls) -> DataFrame:
        """
        Fetches and validates Orderbook Reward DataFrame as concatenation from Prod and Staging DB
        """
        cow_reward_query = """
        select replace(lower(uid::text), '\\x', '0x') as uid,
               date_part('epoch', creation_timestamp)::integer as creation_time
        from trades
        inner join orders
          on uid = order_uid
        """
        barn, prod = cls._query_both_dbs(cow_reward_query)
        return pd.concat([prod, barn])
