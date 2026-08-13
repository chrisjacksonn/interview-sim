"""Samples. Passing these is not the grade."""

import unittest

from solution import Checkout


class TestCheckoutRules(unittest.TestCase):
    def test_deal_with_a_leftover(self):
        till = Checkout()
        till.set_price("apple", 50)
        till.set_deal("apple", 3, 130)
        for _ in range(4):
            till.scan("apple")
        self.assertEqual(till.total(), 180)

    def test_a_new_price_reaches_the_basket(self):
        till = Checkout()
        till.set_price("apple", 50)
        till.set_deal("apple", 3, 130)
        for _ in range(4):
            till.scan("apple")
        till.set_price("apple", 60)
        self.assertEqual(till.total(), 190)

    def test_an_unpriced_sku(self):
        till = Checkout()
        self.assertIs(till.scan("ghost"), False)
        self.assertEqual(till.total(), 0)


if __name__ == "__main__":
    unittest.main()
