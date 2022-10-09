import json
import unittest
import shutil

from src.utils import partition_array, write_to_json


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.path = "./tmp"
        self.filename = "test-file"

    def tearDown(self) -> None:
        # Remove test file directory
        try:
            shutil.rmtree(self.path)
        except FileNotFoundError as err:
            print(err)

    def test_partition_array(self):
        self.assertEqual(partition_array([1, 2, 3, 4], 2), [[1, 2], [3, 4]])

    def test_write_to_json(self):
        data_dict = {"1": [2, 3], "4": {"5": "6"}}
        write_to_json(data_dict, self.path, self.filename)

        with open(f"{self.path}/{self.filename}", 'r') as new_file:
            self.assertEqual(json.load(new_file), data_dict)


if __name__ == "__main__":
    unittest.main()
