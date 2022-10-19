import os

import click
import pandas as pd
from dotenv import load_dotenv
from web3 import Web3

from src.db.pg_client import pg_engine


@click.command()
@click.option(
    "--batch_tx_hash",
    help="The transaction hash of the batch you want to see the % gas saved.",
    type=str,
)
def main(batch_tx_hash):
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
    print(
        f"Trades executed individually would have cost {df_quotes['gas_amount'].sum():.0f} gas."
    )
    print(f"Batch only used {tx.gasUsed} gas.")
    print(
        f"This resulted in {df_quotes['gas_amount'].sum() - tx.gasUsed:.0f} absolute gas saved and "
        f"{((df_quotes['gas_amount'].sum() - tx.gasUsed) / df_quotes['gas_amount'].sum()) * 100:.2f}% decrease of gas."
    )
    return 0


if __name__ == "__main__":
    main()
