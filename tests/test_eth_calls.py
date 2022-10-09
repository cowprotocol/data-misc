import unittest

from src.subgraph.ens_data import read_ens_text


class MyTestCase(unittest.TestCase):
    def test_read_ens_text(self):
        # {
        #     "violet-milan.eth": {
        #         "id": "0x8614e69abc84c8a2a94092d76ed5b7831ae80d69c677746eded3ac9ee4f80662",
        #         "texts": ["avatar", "description", "com.github"],
        #     }
        # }
        texts = ["avatar", "description", "com.github"]
        expected = [
            "https://i.pinimg.com/originals/8c/ea/0d/8cea0db2822dab06989e7de121256c92.jpg",
            "here dwells Violet",
            "https://nimi.eth.limo/",
        ]
        node = "0x8614e69abc84c8a2a94092d76ed5b7831ae80d69c677746eded3ac9ee4f80662"
        public_resolver = "0x4976fb03c32e5b8cfe2b6ccb31c09ba78ebaba41"
        for text, value in zip(texts, expected):
            self.assertEqual(
                read_ens_text(
                    resolver=public_resolver,
                    node=node,
                    key=text,
                ),
                value,
                f"Failed assertion on text field '{text}'",
            )


if __name__ == "__main__":
    unittest.main()
