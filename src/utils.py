import argparse
import json
import os
from datetime import datetime
from enum import Enum
from typing import Any
from dataclasses import dataclass

from dune_client.types import Address
from marshmallow import fields, Schema, post_load, ValidationError


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


class EthereumAddress(fields.Field):
    """Field that serializes to a string of numbers and deserializes
    to a list of numbers.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return f"{value}".lower()

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return Address(value)
        except ValueError as error:
            raise ValidationError("Not a valid address") from error


@dataclass
class Token:
    """Dataclass for holding Token data"""

    address: Address
    decimals: int
    symbol: str
    popularity: int


@dataclass
class Coin:
    """Dataclass for holding Coin data"""

    id: str
    name: str
    symbol: str
    rank: int
    is_new: bool
    is_active: bool
    type: str
    address: Address


class TokenSchema(Schema):
    """TokenSchema CoinSchema for serializing/deserializing token data"""

    address = EthereumAddress(required=True)
    decimals = fields.Int(required=True)
    popularity = fields.Int()
    symbol = fields.String()

    @post_load
    def make_token(self, data, **_kwargs):
        """Turns Token data into Token instance"""
        return Token(**data)


class CoinSchema(Schema):
    """CoinSchema for serializing/deserializing coin data"""

    # pylint: disable=too-many-instance-attributes
    # Eight are passed from the API

    id = fields.String(required=True)
    name = fields.String()
    symbol = fields.String(required=True)
    rank = fields.Int()
    is_new = fields.Bool()
    is_active = fields.Bool()
    type = fields.String()
    address = EthereumAddress(required=True)

    def load(self, *args, **kwargs):
        try:
            return super().load(*args, **kwargs)
        except ValidationError as e:
            return e.valid_data

    @post_load
    def make_coin(self, data, **_kwargs):
        """Turns Coin data into Coin instance"""
        return Coin(**data)


class CoinsSchema(fields.Dict):
    """CoinsSchema for containing multiple Coinschema-s"""

    @staticmethod
    def _get_obj(obj, _attr, _default):
        """Accessor for the dump method"""
        return obj

    def dump(self, obj: Any):
        """Serializes data"""
        return self.serialize("", obj, accessor=self._get_obj)

    def load(self, data: dict[Address, Any]):
        """Loads data into mapping"""
        try:
            return self.deserialize(data)
        except ValidationError as e:
            return e.valid_data
