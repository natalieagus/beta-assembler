import unittest

from helper_functions import is_number
from parameterized import parameterized


class TestHelperFunctions(unittest.TestCase):
    @parameterized.expand([[bin(i), [i]] for i in range(0, 2**8)])
    def test_is_number_binary(self, a, b):
        self.assertEqual(is_number(a), b)

    @parameterized.expand([[hex(i), [i]] for i in range(0, 2**8)])
    def test_is_number_hex(self, a, b):
        self.assertEqual(is_number(a), b)

    @parameterized.expand([[str(i), [i]] for i in range(0, 2**8)])
    def test_is_number_decimal(self, a, b):
        self.assertEqual(is_number(a), b)

    @parameterized.expand(
        [["abc", False], ["0h123", False], ["00a", False], ["12 34", False]]
    )
    def test_is_number_invalid(self, a, b):
        self.assertEqual(is_number(a), b)


if __name__ == "__main__":
    unittest.main()
