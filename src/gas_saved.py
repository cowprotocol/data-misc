import click
import pandas as pd
from dotenv import load_dotenv
from eth_typing.encoding import HexStr
from web3 import Web3
from web3.types import TxReceipt

from src.db.pg_client import pg_engine


@click.command()
@click.option(
    "--batch_tx_hash",
    help="The transaction hash of the batch you want to see the % gas saved.",
    type=str,
)
def main(batch_tx_hash: str) -> int:
    """
    Fetches gas saved for a given transaction hash.
    """
    db_engine = pg_engine()
    gas_quotes_query = f"""
    SELECT orders.id::bytea, order_quotes.gas_amount, order_quotes.gas_price
    FROM
        solver_competitions,
        jsonb_to_recordset(solver_competitions.json->'solutions'->-1->'orders') AS orders(id text)
    LEFT JOIN order_quotes ON order_quotes.order_uid = ('\\' || LTRIM(orders.id::text, '0'))::bytea
    WHERE
      solver_competitions.tx_hash = '\\{batch_tx_hash[1:]}'
    """
    df_quotes = pd.read_sql(gas_quotes_query, db_engine)
    # subtract settlement_overhead from price estimation
    # pylint:disable=line-too-long
    # Ref: https://github.com/cowprotocol/services/blob/fd5f7cf47a6afdff89b310b60b869dfc577ac7a7/crates/shared/src/price_estimation/gas.rs#L37
    df_quotes["gas_amount"] = df_quotes["gas_amount"].apply(lambda x: x - 106391)
    load_dotenv()
    w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))
    tx: TxReceipt = w3.eth.get_transaction_receipt(HexStr(batch_tx_hash))
    gas_used = tx["gasUsed"]
    print(
        f"Trades executed individually would have cost {df_quotes['gas_amount'].sum():.0f} gas."
    )
    print(f"Batch only used {gas_used} gas.")
    sum_gas = df_quotes["gas_amount"].sum()
    gas_saved = sum_gas - gas_used
    decrease = (gas_saved / sum_gas) * 100
    print(
        f"This resulted in {gas_saved:.0f} absolute gas saved and {decrease:.2f}% decrease of gas."
    )
    return 0


if __name__ == "__main__":
    # TODO - figure out how to get this linted with the click decorator!
    # pylint:disable=no-value-for-parameter
    main()
