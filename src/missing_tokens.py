import os

import web3.exceptions
from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.query import Query as DuneQuery
from dune_client.types import QueryParameter

from duneapi.types import Address
from web3 import Web3

from src.constants import ERC20_ABI
from src.utils import Network


class TokenDetails:  # pylint:disable=too-few-public-methods
    """EVM token Details (including address, symbol, decimals)"""

    def __init__(self, address: Address, w3: Web3):
        self.address = Web3.toChecksumAddress(address.address)
        if self.address == Web3.toChecksumAddress(
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
        ):
            self.symbol = "ETH"
            self.decimals = 18
        else:
            token_contract = w3.eth.contract(address=self.address, abi=ERC20_ABI)
            self.symbol = token_contract.caller.symbol()
            self.decimals = token_contract.caller.decimals()

    def as_dune_string(self) -> str:
        """
        Returns Dune Representation of an ERC20 Token:
        https://github.com/duneanalytics/spellbook/blob/main/models/tokens/ethereum/tokens_ethereum_erc20.sql
        Example:
          ('0xfcc5c47be19d06bf83eb04298b026f81069ff65b', 'yCRV', 18),
        """
        return f",('{str(self.address).lower()}', '{self.symbol}', {self.decimals})"


def fetch_missing_tokens(dune: DuneClient, network: Network) -> list[Address]:
    """Uses Official DuneAPI and to fetch Missing Tokens"""
    query = DuneQuery(
        name="V3: Missing Tokens on {{Blockchain}}",
        query_id=2444707,
        params=[
            QueryParameter.enum_type("Blockchain", network.as_dune_v2_repr()),
            QueryParameter.date_type("DateFrom", "2023-01-01 00:00:00"),
            QueryParameter.number_type("Popularity", 250),
        ],
    )
    print(f"Fetching missing tokens for {network} from {query.url()}")
    v2_missing = dune.refresh(query, ping_frequency=10)

    return [Address(row["token"]) for row in v2_missing.get_rows()]


def run_missing_tokens(chain: Network) -> None:
    """Script's main entry point, runs for given network."""
    w3 = Web3(Web3.HTTPProvider(chain.node_url(os.environ["INFURA_KEY"])))
    client = DuneClient(os.environ["DUNE_API_KEY"])
    missing_tokens = fetch_missing_tokens(client, chain)

    if missing_tokens:
        print(f"Found {len(missing_tokens)} missing tokens. Fetching details...\n")
        token_details: dict[Address, TokenDetails] = {}
        ignored = set()
        for token in missing_tokens:
            try:
                # TODO batch the eth_calls used to construct the token contracts.
                token_details[token] = TokenDetails(address=token, w3=w3)
            except web3.exceptions.BadFunctionCallOutput:
                ignored.add(token)
                print(f"BadFunctionCallOutput on {token} - skipping.")
            except web3.exceptions.ContractLogicError:
                ignored.add(token)
                print(f"ContractLogicError on {token} - skipping.")

        results = "\n".join(
            token_details[t].as_dune_string()
            for t in missing_tokens
            if t not in ignored
        )[
            :-1
        ]  # slice-off the last comma!
        print(f"Missing Tokens:\n\n{results}\n")
    else:
        print(f"No missing tokens detected on {chain}. Have a good day!")


if __name__ == "__main__":
    load_dotenv()
    for blockchain in list(Network):
        print(f"Execute on Network {blockchain}")
        run_missing_tokens(chain=blockchain)
