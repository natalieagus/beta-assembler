import unittest

from parameterized import parameterized
from shunting_yard import convert, evaluate


class TestShuntingYard(unittest.TestCase):
    @parameterized.expand(
        [
            [["1 + 2 - 3", 0, {}], "1 2 3 - +"],
            [["1 + 2 * 3", 0, {}], "1 2 3 * +"],
            [["1 + 2 * 3 + 4", 0, {}], "1 2 3 * 4 + +"],
            [["1 + 2 * 3 + 4 - 5", 0, {}], "1 2 3 * 4 5 - + +"],
        ]
    )
    def test_convert(self, a, b):
        # TODO: Double check this implementation
        self.assertEqual(convert(*a), b)

    @parameterized.expand(
        [
            [["1 + 2 - 3", 0, {}], "0"],
            [["1 + 2 * 3", 0, {}], "7"],
            [["1 + 2 * 3 + 4", 0, {}], "11"],
            [["1 + 2 * 3 + 4 - 5", 0, {}], "6"],
        ]
    )
    def test_evaluate(self, a, b):
        self.assertEqual(evaluate(*a), b)


if __name__ == "__main__":
    unittest.main()
