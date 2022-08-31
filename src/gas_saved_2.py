import os

import click
import pandas as pd
from dotenv import load_dotenv
from web3 import Web3

from src.db.pg_client import pg_engine

from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network
from duneapi.util import open_query


def fetch_trades_per_batch(dune: DuneAPI):
    query = DuneQuery.from_environment(
        raw_sql=open_query("./queries/num-trades-per-batch.sql"),
        name="num-trades-per-batch",
        network=Network.MAINNET,
        parameters=[],
    )
    results = dune.fetch(query)
    return results


def get_percentage_gas_used_of_estimate(batch_tx_hash):
    db_engine = pg_engine()
    GAS_QUOTES_QUERY = f"""
    SELECT orders.id::bytea, order_quotes.gas_amount, order_quotes.gas_price
    FROM
        solver_competitions,
        jsonb_to_recordset(solver_competitions.json->'solutions'->-1->'orders') AS orders(id text)
    LEFT JOIN order_quotes ON order_quotes.order_uid = ('\\' || LTRIM(orders.id::text, '0'))::bytea
    WHERE
      solver_competitions.tx_hash = '\\{batch_tx_hash[1:]}'
    """
    df_quotes = pd.read_sql(GAS_QUOTES_QUERY, db_engine)
    # subtract settlement_overhead from price estimation
    # Ref: https://github.com/cowprotocol/services/blob/fd5f7cf47a6afdff89b310b60b869dfc577ac7a7/crates/shared/src/price_estimation/gas.rs#L37
    df_quotes["gas_amount"] = df_quotes["gas_amount"].apply(lambda x: x - 106391)
    load_dotenv()
    w3 = Web3(
        Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.environ['INFURA_KEY']}")
    )
    tx = w3.eth.get_transaction_receipt(batch_tx_hash)
    if df_quotes['gas_amount'].sum() == 0:
        return -1
    print(batch_tx_hash)
    print(tx.gasUsed/df_quotes['gas_amount'].sum())
    return tx.gasUsed/df_quotes['gas_amount'].sum()



if __name__ == "__main__":
    dune_conn = DuneAPI.new_from_environment()
    df = fetch_trades_per_batch(dune_conn)
    data = {'tx_hash': [], 'num_trades': [], 'gas_percentage': []}
    df_result = pd.DataFrame(data)
    for i in df:
        new_row = {'tx_hash':i['txhash'], 'num_trades':i['num_trades'], 'gas_percentage':get_percentage_gas_used_of_estimate(i['txhash'])}
        df_result = df_result.append(new_row, ignore_index=True)
    
    print(df_result[df_result.gas_percentage > 0].groupby('num_trades')['gas_percentage'].mean())