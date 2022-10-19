import unittest

from src.subgraph.ens_data import get_wallet_ens_data


class MyTestCase(unittest.TestCase):
    def test_fetch_ens_data_small(self):
        expected_ens_records = {
            "0xff16d64179a02d6a56a1183a28f1d6293646e2dd": [
                {
                    "paratune.eth": {
                        "id": "0x0a9ec1c5b32be3e1abde5151e2b63c994bede018bbb423af7eeb965297620f04",
                        "texts": {"url": "https://www.twitch.tv/paratune"},
                    }
                }
            ],
            "0xec0297f0a72286c92e826e3b55bd61ad31986dfe": [
                {
                    "degentogetherstrong.eth": {
                        "id": "0x0e75676f35b7acb0ccc564d8e382ce459ba6c7b5d73314fff18e9a0dd919b125",
                        "texts": {
                            "avatar": "eip155:1/erc1155:0xB9e9B77C5a930903c4fB0c34b6E2bb2c7Dc90d75/57",
                            "com.twitter": "@degentogetherstrong",
                            "org.telegram": "@kenzo1985",
                            "eth.ens.delegate": "https://discuss.ens.domains/t/ens-dao-delegate-applications/815/732",
                        },
                    }
                }
            ],
        }
        results = get_wallet_ens_data(set(expected_ens_records.keys()), 15687500)
        for wallet, data in expected_ens_records.items():
            self.assertEqual(results[wallet], data, f"failed for wallet {wallet}")


if __name__ == "__main__":
    unittest.main()
