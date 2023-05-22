import argparse
import json
import os
import unittest
import shutil
from datetime import datetime

from duneapi.types import Network as LegacyDuneNetwork

from src.missing_tokens import Network
from src.utils import partition_array, write_to_json, valid_date


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.path = "./tmp"
        os.mkdir(self.path)
        self.filename = "test-file"

    def tearDown(self) -> None:
        # Remove test file directory
        try:
            shutil.rmtree(self.path)
        except FileNotFoundError as err:
            print(err)

    def test_partition_array(self):
        self.assertEqual(partition_array([1, 2, 3, 4], 2), [[1, 2], [3, 4]])
        self.assertEqual(partition_array([1, 2, 3], 2), [[1, 2], [3]])

    def test_write_to_json(self):
        data_dict = {"1": [2, 3], "4": {"5": "6"}}
        write_to_json(data_dict, self.path, self.filename)

        with open(f"{self.path}/{self.filename}.json", "r") as new_file:
            self.assertEqual(json.load(new_file), data_dict)

    def test_valid_date(self):
        date_str = "1985-03-10"
        self.assertEqual(valid_date(date_str), datetime.strptime(date_str, "%Y-%m-%d"))
        with self.assertRaises(argparse.ArgumentTypeError):
            valid_date("Invalid Date")

    def test_network_class(self):
        gnosis = Network.GNOSIS
        mainnet = Network.MAINNET

        self.assertEqual(gnosis.chain_id, 100)
        self.assertEqual(mainnet.chain_id, 1)

        self.assertEqual(gnosis.node_url("FakeKey"), "https://rpc.gnosischain.com")
        self.assertEqual(
            mainnet.node_url("FakeKey"), "https://mainnet.infura.io/v3/FakeKey"
        )

        self.assertEqual(gnosis.as_dune_v2_repr(), "gnosis")
        self.assertEqual(mainnet.as_dune_v2_repr(), "ethereum")


if __name__ == "__main__":
    unittest.main()
