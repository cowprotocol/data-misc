import argparse
import json
import os
from datetime import datetime
from typing import Any

from duneapi.types import Network as LegacyDuneNetwork
from enum import Enum


def partition_array(arr: list[Any], size: int) -> list[list[Any]]:
    return [arr[i : i + size] for i in range(0, len(arr), size)]


def write_to_json(results: dict[Any, Any], path: str, filename: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)
        print(f"Results written to {filename}")


def valid_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        msg = "not a valid date: {0!r}".format(date_str)
        raise argparse.ArgumentTypeError(msg)


class DuneVersion(Enum):
    V1 = "1"
    V2 = "2"


class Network(Enum):
    MAINNET = "mainnet"
    GNOSIS = "gnosis"

    def as_dune_v1_repr(self) -> LegacyDuneNetwork:
        return {
            Network.MAINNET: LegacyDuneNetwork.MAINNET,
            Network.GNOSIS: LegacyDuneNetwork.GCHAIN,
        }[self]

    def as_dune_v2_repr(self) -> str:
        return {Network.MAINNET: "ethereum", Network.GNOSIS: "gnosis"}[self]

    @property
    def node_url(self) -> str:
        return {
            Network.MAINNET: f"https://mainnet.infura.io/v3/{os.environ['INFURA_KEY']}",
            Network.GNOSIS: "https://rpc.gnosischain.com",
        }[self]

    @property
    def chain_id(self) -> int:
        return {Network.MAINNET: 1, Network.GNOSIS: 100}[self]
