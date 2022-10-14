import argparse
import os
from dataclasses import dataclass
from enum import Enum

import web3.exceptions
from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.query import Query as DuneQuery
from dune_client.types import QueryParameter

from duneapi.types import Address
from web3 import Web3

from src.constants import ERC20_ABI
from src.utils import Network

V1_QUERY = DuneQuery(name="V1: Missing Tokens", query_id=1317323)


class DuneVersion(Enum):
    V1 = "1"
    V2 = "2"


class TokenDetails:
    def __init__(self, address: Address):
        self.address = Web3.toChecksumAddress(address.address)
        if self.address == Web3.toChecksumAddress("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"):
            self.symbol = "ETH"
            self.decimals = 18
        else:
            token_contract = w3.eth.contract(address=self.address, abi=ERC20_ABI)
            self.symbol = token_contract.caller.symbol()
            self.decimals = token_contract.caller.decimals()

    def to_str(self, version: DuneVersion):
        if version == DuneVersion.V1:
            self.as_v1_string()
        if version == DuneVersion.V2:
            return self.as_v2_string()
        raise ValueError(f"Invalid DuneVersion {version}")

    def as_v1_string(self) -> str:
        """Returns Dune V1 Representation of an ERC20 Token"""
        address_bytea = f"\\\\x{self.address[2:]}"
        return f"{address_bytea}\t{self.symbol}\t{self.decimals}"

    def as_v2_string(self) -> str:
        """Returns Dune V2 Representation of an ERC20 Token"""
        return f"('{self.address.lower()}', '{self.symbol}', {self.decimals}),"


@dataclass
class MissingTokenResults:
    v1: list[Address]
    v2: list[Address]

    def is_empty(self) -> bool:
        return self.v1 is [] and self.v2 is []

    def get_all_tokens(self) -> set[Address]:
        return set(self.v1 + self.v2)


def fetch_missing_tokens_legacy(dune: DuneClient, network: Network) -> list[Address]:
    query = DuneQuery(
        name="V1: Missing Tokens",
        query_id={Network.MAINNET: 1317323, Network.GNOSIS: 1403053}[network],
    )
    print(f"Fetching V1 missing tokens for {network} from {query.url()}")
    v1_missing = dune.refresh(query)
    return [Address(row["token"]) for row in v1_missing]


def fetch_missing_tokens(dune: DuneClient, network: Network) -> list[Address]:
    query = DuneQuery(
        name="V2: Missing Tokens",
        query_id=1403073,
        params=[QueryParameter.enum_type("Blockchain", network.dune_v2_repr())],
    )
    print(f"Fetching V2 missing tokens for {network} from {query.url()}")
    v2_missing = dune.refresh(query)

    return [Address(row["token"]) for row in v2_missing]


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser("Missing Tokens")
    parser.add_argument(
        "--network",
        type=Network,
        choices=list(Network),
        default=Network.MAINNET,
        help="Blockchain for which we would like to run this script",
    )
    args = parser.parse_args()

    chain: Network = args.network
    w3 = Web3(Web3.HTTPProvider(chain.node_url()))

    missing_tokens = MissingTokenResults(
        v1=fetch_missing_tokens_legacy(DuneClient(os.environ["DUNE_API_KEY"]), chain),
        v2=fetch_missing_tokens(DuneClient(os.environ["DUNE_API_KEY"]), chain),
    )

    if not missing_tokens.is_empty():
        print(
            f"Found {len(missing_tokens.v1)} missing tokens on V1 "
            f"and {len(missing_tokens.v2)} on V2. Fetching token details...\n"
        )
        token_details = {}
        for token in missing_tokens.get_all_tokens():
            try:
                # TODO batch the eth_calls used to construct the token contracts.
                token_details[token] = TokenDetails(address=token)
            except web3.exceptions.BadFunctionCallOutput as err:
                print(f"Something wrong with token {token} - skipping.")

        v1_results = "\n".join(
            token_details[t].as_v1_string() for t in missing_tokens.v1
        )
        v2_results = "\n".join(
            token_details[t].as_v2_string() for t in missing_tokens.v2
        )

        print(f"V1 results:\n\n{v1_results}\n")
        print(f"V2 results:\n\n{v2_results}\n")
        # TODO - write to file!
    else:
        print("No missing tokens detected. Have a good day!")
