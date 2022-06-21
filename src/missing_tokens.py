import os

from dotenv import load_dotenv
from duneapi.api import DuneAPI
from duneapi.types import Address, DuneQuery, Network
from duneapi.util import open_query
from web3 import Web3

from web3.contract import ConciseContract as Factory

from src.constants import ERC20_ABI


class TokenDetails:
    def __init__(self, address: Address):
        self.address = address.address
        token_contract = w3.eth.contract(
            address=Web3.toChecksumAddress(self.address),
            abi=ERC20_ABI,
            ContractFactoryClass=Factory,
        )
        self.symbol = token_contract.symbol()
        self.decimals = token_contract.decimals()

    def __str__(self):
        address_bytea = f"\\\\x{self.address[2:]}"
        return f"{address_bytea}\t{self.symbol}\t{self.decimals}"


def fetch_missing_tokens(dune: DuneAPI) -> list[Address]:
    """Initiates and executes Dune query for affiliate data on given month"""
    query = DuneQuery.from_environment(
        raw_sql=open_query("./queries/missing-tokens.sql"),
        name=f"Missing Tokens",
        network=Network.MAINNET,
        parameters=[],
    )
    results = dune.fetch(query)
    return [Address(row["token"]) for row in results]


if __name__ == "__main__":
    load_dotenv()
    w3 = Web3(
        Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.environ['INFURA_KEY']}")
    )
    dune_conn = DuneAPI.new_from_environment()
    print("Getting missing tokens from: https://dune.com/queries/236085")
    missing_tokens = fetch_missing_tokens(dune_conn)
    if missing_tokens:
        print(f"Found {len(missing_tokens)} missing tokens, fetching metadata...")
        # TODO batch the eth_calls used to construct the token contracts.
        token_details = [str(TokenDetails(address=t)) for t in missing_tokens]
        print("\n".join(token_details))
    else:
        print("No missing tokens detected. Have a good day!")
