from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass

import requests
import yaml

from duneapi.api import DuneAPI
from duneapi.types import Address, DuneQuery, Network
from duneapi.util import open_query


# Begin Hack
# This little block is a hack to get the address (as a number) to print without quotes.
class HexInt(int):
    pass


def representer(dumper, data):
    result = yaml.ScalarNode("tag:yaml.org,2002:int", "0x{:040x}".format(data))
    return result


yaml.add_representer(HexInt, representer)
# End Hack


def load_coins() -> dict[str, dict]:
    entries = requests.get(
        url="https://api.coinpaprika.com/v1/contracts/eth-ethereum", timeout=10
    ).json()
    contract_dict = {}
    for entry in entries:
        if entry["type"] == "ERC20" and entry["active"]:
            # only include ethereum tokens
            contract_dict[entry["id"]] = entry["address"]

    entries = requests.get(
        url="https://api.coinpaprika.com/v1/coins", timeout=10
    ).json()
    coin_dict = {}
    missed = 0
    for entry in entries:
        if entry["type"] == "token" and entry["is_active"]:
            # only include ethereum tokens
            try:
                entry["address"] = contract_dict[entry["id"]].lower()
                coin_dict[entry["address"]] = entry
            except KeyError as err:
                missed += 1
                # print(f"Error with {err}, excluding entry {entry}")

    print(f"Excluded address for {missed} entries out of {len(entries)}")
    return coin_dict


def write_results(results: list[tuple], path: str, filename: str):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w") as file:
        for row in results:
            file.write(str(row) + ",\n")
        print(f"Results written to {filename}")


@dataclass
class Token:
    address: Address
    decimals: int
    symbol: str
    popularity: int

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Token:
        return cls(
            address=Address(data["address"]),
            decimals=int(data["decimals"]),
            symbol=data["symbol"],
            popularity=int(data["popularity"]),
        )

    def __str__(self):
        return (
            f"Token("
            f"address={self.address}, "
            f"decimals = {self.decimals}, "
            f"symbol = {self.symbol}, "
            f"popularity = {self.popularity})"
        )

    def coin_paprika_rep(self, coin_id: str) -> dict:
        return {
            # dune uses the snake case id as the name
            "name": coin_id.replace("-", "_"),
            "id": coin_id,
            "symbol": self.symbol,
            "address": HexInt(int(str(self.address), 16)),
            "decimals": self.decimals,
        }


def load_tokens(path: str):
    with open(path, encoding="utf-8") as csv_f:
        reader = csv.DictReader(csv_f)
        return [row for row in reader]


def fetch_tokens_without_prices(dune: DuneAPI) -> list[Token]:
    """Initiates and executes Dune query for affiliate out on given month"""
    query = DuneQuery.from_environment(
        raw_sql=open_query("./queries/traded-tokens-without-prices.sql"),
        name="Traded Tokens Without Prices",
        network=Network.MAINNET,
        parameters=[],
    )
    results = dune.fetch(query)
    return [Token.from_dict(r) for r in results]


if __name__ == "__main__":
    print("Getting Coin Paprika token list")
    coins = load_coins()
    print(f"Loaded {len(coins)} coins from Coin Paprika")

    tokens = load_tokens("out/missing-token-prices.csv")
    print(f"Fetched {len(tokens)} traded tokens from Dune without prices")
    found, res = 0, []
    for token in tokens:
        if token["address"].lower() in coins:
            paprika_data = coins[token["address"].lower()]
            dune_row = (
                paprika_data["id"],
                "ethereum",
                paprika_data["symbol"],
                paprika_data["address"].lower(),
                int(token["decimals"]),
            )
            res.append(dune_row)
            found += 1
    print(f"Found {found} matches")
    write_results(results=res, path="./out", filename="missing-prices.txt")
