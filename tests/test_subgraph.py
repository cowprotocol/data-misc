import unittest

from src.subgraph.ens_data import get_names_for_wallets


class MyTestCase(unittest.TestCase):
    def test_fetch_ens_data_small(self):
        expected_ens_records = {
            "0xd819c62dde216ef3b508d348542b59477efd606f": [
                {
                    "billionmonero.eth": {
                        "id": "0x80728c5e7dc6351b957842bffcd2b2fd81a33161be2414bcd6a5ec19e375ff43",
                        "texts": [
                            "avatar",
                            "description",
                            "com.twitter"
                        ]
                    }
                },
                {
                    "\u20bfillion.eth": {
                        "id": "0xedcd26fb14b816aaa75f126417a30aeed74e0791db0fbd20161f0760c5c1b054",
                        "texts": [
                            "avatar",
                            "com.twitter"
                        ]
                    }
                }
            ],
            "0x4532280a66a0c1c709f7e0c40b14b4dea83253c1": [
                {
                    "this.tokenid.eth": {
                        "id": "0x73894c93620b73274a8142880ac8ba2712b01b455b069d4caac0932e44143810",
                        "texts": [
                            "vnd.twitter",
                            "vnd.github",
                            "url",
                            "email",
                            "avatar"
                        ]
                    }
                },
                {
                    "rsivakov.eth": {
                        "id": "0xe198e18ea0f413453317c9bffab86f1ab5d2e395ff9e3256aa7daa808194dc93",
                        "texts": [
                            "vnd.twitter",
                            "vnd.github",
                            "url",
                            "email",
                            "avatar",
                            "notice",
                            "description",
                            "keywords",
                            "com.twitter",
                            "com.github",
                            "com.discord",
                            "com.reddit",
                            "org.telegram",
                            "eth.ens.delegate"
                        ]
                    }
                },
                {
                    "samiznaetekto.eth": {
                        "id": "0xfb522aba5a07c39a0ff9a95b43b09c86f2d7c5c484e4207f1b9637dea1b79fb8",
                        "texts": [
                            "url",
                            "vnd.github"
                        ]
                    }
                }
            ],
            "0xff16d64179a02d6a56a1183a28f1d6293646e2dd": [
                {
                    "paratune.eth": {
                        "id": "0x0a9ec1c5b32be3e1abde5151e2b63c994bede018bbb423af7eeb965297620f04",
                        "texts": ["url"],
                    }
                }
            ],
            "0xec0297f0a72286c92e826e3b55bd61ad31986dfe": [
                {
                    "degentogetherstrong.eth": {
                        "id": "0x0e75676f35b7acb0ccc564d8e382ce459ba6c7b5d73314fff18e9a0dd919b125",
                        "texts": [
                            "avatar",
                            "com.twitter",
                            "org.telegram",
                            "eth.ens.delegate",
                        ],
                    }
                }
            ],
            "0xc47fae56f3702737b69ed615950c01217ec5c7c8": [
                {
                    "fulmer.eth": {
                        "id": "0x107dc1e72a3f3529757ec494a66dcd794aaf6f75ad793f540c842aea826fe5d1",
                        "texts": ["com.discord", "avatar"],
                    }
                }
            ],
        }
        results = get_names_for_wallets(set(expected_ens_records.keys()), 15687500)
        for wallet, data in expected_ens_records.items():
            self.assertEqual(results[wallet], data, f"failed for wallet {wallet}")


if __name__ == "__main__":
    unittest.main()
