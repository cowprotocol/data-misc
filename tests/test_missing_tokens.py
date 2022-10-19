import unittest

from dune_client.types import Address

from src.missing_tokens import MissingTokenResults


class TestMissingTokens(unittest.TestCase):
    def setUp(self) -> None:
        self.tokens = list(map(Address.from_int, range(3)))
        print(self.tokens)
        t0, t1, t2 = self.tokens[0], self.tokens[1], self.tokens[2]
        self.left = MissingTokenResults(v1=[t0], v2=[])
        self.right = MissingTokenResults(v1=[], v2=[t1])
        self.both = MissingTokenResults(v1=[t0], v2=[t1])
        self.neither = MissingTokenResults(v1=[], v2=[])
        self.overlap = MissingTokenResults(v1=[t0, t1], v2=[t1, t2])

    def test_is_empty(self):
        self.assertEqual(self.left.is_empty(), False)
        self.assertEqual(self.right.is_empty(), False)
        self.assertEqual(self.both.is_empty(), False)
        self.assertEqual(self.neither.is_empty(), True)
        self.assertEqual(self.overlap.is_empty(), False)

    def test_all_tokens(self):
        t0, t1, t2 = self.tokens[0], self.tokens[1], self.tokens[2]
        self.assertEqual(self.left.get_all_tokens(), {t0})
        self.assertEqual(self.right.get_all_tokens(), {t1})
        self.assertEqual(self.both.get_all_tokens(), {t0, t1})
        self.assertEqual(self.neither.get_all_tokens(), set())
        self.assertEqual(self.overlap.get_all_tokens(), {t0, t1, t2})


if __name__ == "__main__":
    unittest.main()
