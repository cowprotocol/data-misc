import csv
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import web3.exceptions
from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.query import Query as DuneQuery

from duneapi.api import DuneAPI
from duneapi.file_io import File
from duneapi.types import Address, DuneQuery as LegacyDuneQuery, Network
from duneapi.util import open_query
from web3 import Web3

from src.constants import ERC20_ABI

V1_QUERY = DuneQuery(name="V1: Missing Tokens", query_id=1317323)
V2_QUERY = DuneQuery(name="V2: Missing Tokens", query_id=1367051)


class DuneVersion(Enum):
    V1 = "1"
    V2 = "2"


class TokenDetails:
    def __init__(self, address: Address):
        self.address = address.address
        token_contract = w3.eth.contract(
            address=Web3.toChecksumAddress(self.address),
            abi=ERC20_ABI,
        )
        self.symbol = token_contract.caller.symbol()
        self.decimals = token_contract.caller.decimals()

    def to_str(self, version: DuneVersion):
        if version == DuneVersion.V1:
            self.v1_string()
        if version == DuneVersion.V2:
            return self.v2_string()
        raise ValueError(f"Invalid DuneVersion {version}")

    def v1_string(self) -> str:
        address_bytea = f"\\\\x{self.address[2:]}"
        return f"{address_bytea}\t{self.symbol}\t{self.decimals}"

    def v2_string(self) -> str:
        return f"('{self.address.lower()}', '{self.symbol}', {self.decimals}),"


def fetch_missing_tokens_legacy(dune: DuneAPI, file: Optional[File]) -> list[Address]:
    """Initiates and executes Dune query for affiliate data on given month"""
    if file:
        # Until we can fetch from DuneV2, this will have to be a file.
        print(f"Loading missing tokens from: {file.filename()}")
        with open(file.filename(), "r") as csv_file:
            return [Address(row["token"]) for row in csv.DictReader(csv_file)]

    print("Getting missing tokens from: https://dune.com/queries/236085")
    query = LegacyDuneQuery.from_environment(
        raw_sql=open_query("./queries/missing-tokens.sql"),
        name=f"Missing Tokens",
        network=Network.MAINNET,
        parameters=[],
    )
    results = dune.fetch(query)
    return [Address(row["token"]) for row in results]


@dataclass
class MissingTokenResults:
    v1: list[Address]
    v2: list[Address]

    def is_empty(self) -> bool:
        return self.v1 is [] and self.v2 is []

    def all_tokens(self) -> set[Address]:
        return set(self.v1 + self.v2)


def fetch_missing_tokens_api(dune: DuneClient) -> MissingTokenResults:
    print(f"Fetching V1 missing tokens from {V1_QUERY.query_id}")
    v1_missing = dune.refresh(V1_QUERY)
    print(f"Fetching V2 missing tokens from {V2_QUERY.query_id}")
    v2_missing = dune.get_result("01GERZ7JW8A29ZXY4R35SS0GXK").result.rows
    # v2_missing = dune.refresh(V2_QUERY)


    return MissingTokenResults(
        v1=[Address(row["token"]) for row in v1_missing],
        v2=[Address(row["token"]) for row in v2_missing],
    )


if __name__ == "__main__":
    load_dotenv()

    w3 = Web3(
        Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.environ['INFURA_KEY']}")
    )
    missing_tokens = fetch_missing_tokens_api(DuneClient(os.environ["DUNE_API_KEY"]))
    print(missing_tokens)
    if not missing_tokens.is_empty():
        print(
            f"Found {len(missing_tokens.v1)} missing tokens on V1 "
            f"and {len(missing_tokens.v2)}, fetching metadata...\n"
        )
        token_details = {}
        for token in missing_tokens.all_tokens():
            try:
                # TODO batch the eth_calls used to construct the token contracts.
                token_details[token] = TokenDetails(address=token)
            except web3.exceptions.BadFunctionCallOutput as err:
                print(f"Something wrong with token {token} - skipping.")

        v1_results = "\n".join(token_details[t].v1_string() for t in missing_tokens.v1)
        v2_results = "\n".join(token_details[t].v2_string() for t in missing_tokens.v2)

        print(f"V1 results:\n{v1_results}")
        print(f"V2 results:\n{v2_results}")
    else:
        print("No missing tokens detected. Have a good day!")
