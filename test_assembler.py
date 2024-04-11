import unittest

from assembler import parse_asm, write_data
from parameterized import parameterized


class TestAssembler(unittest.TestCase):
    @parameterized.expand(
        [
            [([1, 2, 3], 0, []), (3, [1, 2, 3])],
            [([], 0, [1, 2, 3]), (0, [1, 2, 3])],
            [([], 0, []), (0, [])],
            [([1, 2, 3], 3, [1, 2, 3]), (6, [1, 2, 3, 1, 2, 3])],
            [([1, 2, 3], 2, [1, 2, 3]), (5, [1, 2, 1, 2, 3])],
            [([1, 2, 3], 0, [1, 2, 3]), (3, [1, 2, 3])],
        ]
    )
    def test_write_data(self, a, b):
        self.assertEqual(write_data(*a), b)

    def test_parse_asm(self):
        self.assertEqual(parse_asm("| this is a comment")[0], [])
        self.assertEqual(parse_asm("LONG(0xDEADBEEF)")[0], ["ef", "be", "ad", "de"])


if __name__ == "__main__":
    unittest.main()
