from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass

import requests
import yaml

from duneapi.api import DuneAPI
from duneapi.types import Address, DuneQuery, Network
from duneapi.util import open_query


# Begin Hack
class HexInt(int):
    """
    This little block is a hack to get the address (as a number) to print without quotes.
    """


# pylint:disable=unused-argument
def representer(dumper, data):
    """Yaml Representer for HexInt"""
    # pylint:disable=consider-using-f-string
    return yaml.ScalarNode("tag:yaml.org,2002:int", "0x{:040x}".format(data))


yaml.add_representer(HexInt, representer)
# End Hack


def load_coins() -> dict[str, list[dict]]:
    """"
    Loads and returns coin dictionaries from Coin Paprika via their API.
    Excludes, inactive, new and non "token" types
    """
    entries = requests.get(
        url="https://api.coinpaprika.com/v1/coins", timeout=10
    ).json()
    coin_dict = defaultdict(list)
    for entry in entries:
        if entry["type"] == "token" and entry["is_active"] and not entry["is_new"]:
            # only include ethereum tokens
            coin_dict[entry["symbol"]].append(entry)
    return coin_dict


def write_results(results: list[dict], path: str, filename: str):
    """
    Writes Results to YAML file: Format compatible with
    https://github.com/duneanalytics/spellbook/blob/main/deprecated-dune-v1-abstractions/prices/ethereum/coinpaprika.yaml
    """
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w", encoding='utf-8') as yaml_file:
        yaml.dump(
            data=results, stream=yaml_file, default_flow_style=False, sort_keys=False
        )
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

    def as_dune_repr(self, coin_id: str) -> dict:
        """Dune YAML representation of CPToken"""
        return {
            # dune uses the snake case id as the name
            "name": coin_id.replace("-", "_"),
            "id": coin_id,
            "symbol": self.symbol,
            "address": HexInt(int(str(self.address), 16)),
            "decimals": self.decimals,
        }


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


def run_missing_prices():
    """Script's Main Entry Point"""
    print("Getting Coin Paprika token list")
    coins = load_coins()
    print(f"Loaded {len(coins)} coins from Coin Paprika")

    # Fetch tokens orders by descending, popularity
    print("Getting traded tokens without prices from: https://dune.com/queries/224239")
    tokens = sorted(
        # Could be interesting to just get the results without executing.
        fetch_tokens_without_prices(dune=DuneAPI.new_from_environment()),
        key=lambda t: t.popularity,
        reverse=True,
    )
    print(f"Fetched {len(tokens)} traded tokens from Dune without prices")
    found, res = 0, []
    for token in tokens:
        if token.symbol in coins:
            possibilities = coins[token.symbol]
            if len(possibilities) == 1:
                res.append(token.as_dune_repr(possibilities[0]["id"]))
                found += 1
            else:
                print(f"non unique {token}: {len(possibilities)} occurrences")
        if found > 50:
            print("Stopped at 50 results.")
            break

    write_results(results=res, path="./out", filename="missing-prices.yaml")


if __name__ == "__main__":
    run_missing_prices()
