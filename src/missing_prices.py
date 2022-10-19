from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from dune_client.client import DuneClient
from dune_client.query import Query
from dune_client.types import DuneRecord

from duneapi.api import DuneAPI
from duneapi.types import Address, DuneQuery, Network
from duneapi.util import open_query


def load_coins() -> dict[str, dict[str, Any]]:
    """ "
    Loads and returns coin dictionaries from Coin Paprika via their API.
    Excludes, inactive, new and non "token" types
    """
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
            except KeyError:
                missed += 1
                # print(f"Error with {err}, excluding entry {entry}")

    print(f"Excluded address for {missed} entries out of {len(entries)}")
    return coin_dict


def write_results(
    results: list[tuple[Any, str, Any, Any, int]], path: str, filename: str
) -> None:
    """Writes results to file"""
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w", encoding="utf-8") as file:
        for row in results:
            file.write(str(row) + ",\n")
        print(f"Results written to {filename}")


@dataclass
class CoinPaprikaToken:
    """Representation of a Coin Paprika Token"""

    address: Address
    decimals: int
    symbol: str
    popularity: int

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> CoinPaprikaToken:
        """Converts Dune Results into CoinPaprikaToken"""
        return cls(
            address=Address(data["address"]),
            decimals=int(data["decimals"]),
            symbol=data["symbol"],
            popularity=int(data["popularity"]),
        )

    def __str__(self) -> str:
        return (
            f"CoinPaprikaToken("
            f"address={self.address}, "
            f"decimals={self.decimals}, "
            f"symbol={self.symbol}, "
            f"popularity={self.popularity})"
        )

    def as_dune_repr(self, coin_id: str) -> dict[str, Any]:
        """Dune YAML representation of CPToken"""
        return {
            # dune uses the snake case id as the name
            "name": coin_id.replace("-", "_"),
            "id": coin_id,
            "symbol": self.symbol,
            "address": str(self.address),
            "decimals": self.decimals,
        }


def load_tokens(dune: DuneClient) -> list[DuneRecord]:
    """Loads Tokens with missing prices from Dune"""
    return dune.refresh(Query(query_id=1317238, name="Tokens with Missing Prices"))


def fetch_tokens_without_prices(dune: DuneAPI) -> list[CoinPaprikaToken]:
    """Initiates and executes Dune query for affiliate out on given month"""
    query = DuneQuery.from_environment(
        raw_sql=open_query("./queries/traded-tokens-without-prices.sql"),
        name="Traded Tokens Without Prices",
        network=Network.MAINNET,
        parameters=[],
    )
    results = dune.fetch(query)
    return [CoinPaprikaToken.from_dict(r) for r in results]


def run_missing_prices() -> None:
    """Script's Main Entry Point"""
    print("Getting Coin Paprika token list")
    coins = load_coins()
    print(f"Loaded {len(coins)} coins from Coin Paprika")

    tokens = load_tokens(DuneClient(api_key=os.environ["DUNE_API_KEY"]))
    print(f"Fetched {len(tokens)} traded tokens from Dune without prices")
    found, res = 0, []
    for token in tokens:
        if token["address"].lower() in coins:
            paprika_data = coins[token["address"].lower()]
            dune_row = (
                str(paprika_data["id"]),
                "ethereum",
                paprika_data["symbol"],
                paprika_data["address"].lower(),
                int(token["decimals"]),
            )
            res.append(dune_row)
            found += 1
    print(f"Found {found} matches")
    write_results(results=res, path="./out", filename="missing-prices.txt")


if __name__ == "__main__":
    run_missing_prices()
