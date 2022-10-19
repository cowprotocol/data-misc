import argparse
import json
import os
from datetime import datetime
from enum import Enum
from typing import Any

from duneapi.types import Network as LegacyDuneNetwork


def partition_array(arr: list[Any], size: int) -> list[list[Any]]:
    """Partitions `arr` into slices of `size` (except possibly the last)
    >>> partition_array([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    """
    return [arr[i : i + size] for i in range(0, len(arr), size)]


def write_to_json(results: dict[Any, Any], path: str, filename: str) -> None:
    """Writes a dictionary to JSON file at the location specified by path and filename"""
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename + ".json"), "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)
        print(f"Results written to {filename}")


def valid_date(date_str: str) -> datetime:
    """
    Returns datetime object from a given string in the form YYYY-MM-DD
    Otherwise, raises
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as err:
        msg = f"not a valid date: {date_str}"
        raise argparse.ArgumentTypeError(msg) from err


class DuneVersion(Enum):
    """Two different Dune Engines"""

    # Postgres
    V1 = "1"
    # Spark/Hive
    V2 = "2"


class Network(Enum):
    """
    Supported chains (generally be a subset of what Dune Supports, but not a hard constraint)
    """

    MAINNET = "mainnet"
    GNOSIS = "gnosis"

    def as_dune_v1_repr(self) -> LegacyDuneNetwork:
        """Returns Dune V1 Network Indicator (as compatible with duneapi)"""
        return {
            Network.MAINNET: LegacyDuneNetwork.MAINNET,
            Network.GNOSIS: LegacyDuneNetwork.GCHAIN,
        }[self]

    def as_dune_v2_repr(self) -> str:
        """Returns Dune V1 Network String (as compatible with Dune V2 Engine)"""
        return {Network.MAINNET: "ethereum", Network.GNOSIS: "gnosis"}[self]

    def node_url(self, api_key: str) -> str:
        """Returns URL to Node for Network"""
        return {
            Network.MAINNET: f"https://mainnet.infura.io/v3/{api_key}",
            Network.GNOSIS: "https://rpc.gnosischain.com",
        }[self]

    @property
    def chain_id(self) -> int:
        """
        Network's Integer chainID.
        Aligned with https://chainlist.org/
        """
        return {Network.MAINNET: 1, Network.GNOSIS: 100}[self]
