import argparse
import csv
import os
from enum import Enum
from typing import Optional

import web3.exceptions
from dotenv import load_dotenv
from duneapi.api import DuneAPI
from duneapi.file_io import File
from duneapi.types import Address, DuneQuery, Network
from duneapi.util import open_query
from web3 import Web3

from web3.contract import ConciseContract as Factory

from src.constants import ERC20_ABI


class DuneVersion(Enum):
    V1 = "1"
    V2 = "2"


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

    def to_str(self, version: DuneVersion):
        if version == DuneVersion.V1:
            address_bytea = f"\\\\x{self.address[2:]}"
            return f"{address_bytea}\t{self.symbol}\t{self.decimals}"
        if version == DuneVersion.V2:
            return f"('{self.address.lower()}', '{self.symbol}', {self.decimals}),"
        raise ValueError(f"Invalid DuneVersion {version}")


def fetch_missing_tokens(dune: DuneAPI, file: Optional[File]) -> list[Address]:
    """Initiates and executes Dune query for affiliate data on given month"""
    if file:
        # Until we can fetch from DuneV2, this will have to be a file.
        print(f"Loading missing tokens from: {file.filename()}")
        with open(file.filename(), "r") as csv_file:
            return [Address(row["token"]) for row in csv.DictReader(csv_file)]

    print("Getting missing tokens from: https://dune.com/queries/236085")
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
    parser = argparse.ArgumentParser("Missing Tokens")
    parser.add_argument(
        "--token-file",
        type=str,
        help="CSV File to read token data from (this is for Dune V2)",
    )
    args = parser.parse_args()

    token_file = File(args.token_file) if args.token_file else None
    # We only supply a token file for Dune V2.
    dune_version = DuneVersion.V1 if not token_file else DuneVersion.V2

    w3 = Web3(
        Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.environ['INFURA_KEY']}")
    )
    dune_conn = DuneAPI.new_from_environment()
    missing_tokens = fetch_missing_tokens(dune_conn, file=token_file)
    if missing_tokens:
        print(f"Found {len(missing_tokens)} missing tokens, fetching metadata...\n")
        token_details = []
        for t in missing_tokens:
            try:
                # TODO batch the eth_calls used to construct the token contracts.
                token_details.append(TokenDetails(address=t).to_str(dune_version))
            except web3.exceptions.BadFunctionCallOutput as err:
                print(f"Something wrong with token {t} - skipping.")
        print("\n".join(token_details))
    else:
        print("No missing tokens detected. Have a good day!")
