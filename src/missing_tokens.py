import argparse
import os
from dataclasses import dataclass

import web3.exceptions
from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.query import Query as DuneQuery
from dune_client.types import QueryParameter

from duneapi.types import Address
from web3 import Web3

from src.constants import ERC20_ABI
from src.utils import Network, DuneVersion

V1_QUERY = DuneQuery(name="V1: Missing Tokens", query_id=1317323)


class TokenDetails:
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

    def to_str(self, version: DuneVersion) -> str:
        if version == DuneVersion.V1:
            self.as_v1_string()
        if version == DuneVersion.V2:
            return self.as_v2_string()
        raise ValueError(f"Invalid DuneVersion {version}")

    def as_v1_string(self, chain: Network) -> str:
        """
        Returns Dune V1 Representation of an ERC20 Token
        mainnet: https://github.com/duneanalytics/spellbook/blob/main/deprecated-dune-v1-abstractions/ethereum/erc20/tokens.sql
        gnosis: https://github.com/duneanalytics/spellbook/blob/main/deprecated-dune-v1-abstractions/xdai/erc20/extended_tokenlist.sql
        """
        symbol, decimals, address = self.symbol, self.decimals, self.address
        if chain == Network.MAINNET:
            # Eg. \\x96B00208911d72eA9f10c3303fF319427A7884C9	BLUE	18
            address_bytea = f"\\\\x{address[2:]}"
            return f"{address_bytea}\t{symbol}\t{decimals}"
        elif chain == Network.GNOSIS:
            # Eg. ('BAND', 18, decode('e154a435408211ac89757b76c4fbe4dc9ed2ef27', 'hex')),
            return f"('{symbol}', {decimals}, decode('{address[2:]}', 'hex')),"

    def as_v2_string(self) -> str:
        """
        Returns Dune V2 Representation of an ERC20 Token:
        https://github.com/duneanalytics/spellbook/blob/main/models/tokens/ethereum/tokens_ethereum_erc20.sql
        """
        # Eg. ('0xfcc5c47be19d06bf83eb04298b026f81069ff65b', 'yCRV', 18),
        return f"('{self.address.lower()}', '{self.symbol}', {self.decimals}),"


@dataclass
class MissingTokenResults:
    v1: list[Address]
    v2: list[Address]

    def is_empty(self) -> bool:
        return not self.v1 and not self.v2

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
        params=[QueryParameter.enum_type("Blockchain", network.as_dune_v2_repr())],
    )
    print(f"Fetching V2 missing tokens for {network} from {query.url()}")
    v2_missing = dune.refresh(query)

    return [Address(row["token"]) for row in v2_missing]


def run(chain: Network) -> None:
    w3 = Web3(Web3.HTTPProvider(chain.node_url))
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
                token_details[token] = TokenDetails(address=token, w3=w3)
            except web3.exceptions.BadFunctionCallOutput as err:
                print(f"Something wrong with token {token} - skipping.")

        v1_results = "\n".join(
            token_details[t].as_v1_string(chain) for t in missing_tokens.v1
        )
        v2_results = "\n".join(
            token_details[t].as_v2_string() for t in missing_tokens.v2
        )

        print(f"V1 results:\n\n{v1_results}\n")
        print(f"V2 results:\n\n{v2_results}\n")
        # TODO - write to file!
    else:
        print(f"No missing tokens detected on {chain}. Have a good day!")


if __name__ == "__main__":
    load_dotenv()
    for blockchain in list(Network):
        print(f"Execute on Network {blockchain}")
        run(chain=blockchain)
