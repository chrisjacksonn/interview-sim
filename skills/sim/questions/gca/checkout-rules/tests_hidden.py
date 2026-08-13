"""Checkout Rules hidden suite.

Never copied into a session workspace.

Weighted toward the two things a working-looking till gets wrong: the leftover
after a deal, and prices that change while the basket already holds the item.
"""

import unittest

from solution import Checkout


class TestCheckoutRules(unittest.TestCase):
    def setUp(self):
        self.till = Checkout()

    # --- prices and scanning ---

    def test_empty_basket(self):
        self.assertEqual(self.till.total(), 0)

    def test_one_item(self):
        self.till.set_price("apple", 50)
        self.assertIs(self.till.scan("apple"), True)
        self.assertEqual(self.till.total(), 50)

    def test_several_of_the_same(self):
        self.till.set_price("apple", 50)
        for _ in range(3):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 150)

    def test_different_items(self):
        self.till.set_price("apple", 50)
        self.till.set_price("bread", 210)
        self.till.scan("apple")
        self.till.scan("bread")
        self.assertEqual(self.till.total(), 260)

    def test_an_unpriced_sku_is_refused(self):
        self.assertIs(self.till.scan("ghost"), False)
        self.assertEqual(self.till.total(), 0)

    def test_scanning_returns_actual_booleans(self):
        self.till.set_price("apple", 50)
        self.assertIsInstance(self.till.scan("apple"), bool)
        self.assertIsInstance(self.till.scan("ghost"), bool)

    def test_skus_are_case_sensitive(self):
        self.till.set_price("Apple", 50)
        self.assertIs(self.till.scan("apple"), False)
        self.assertIs(self.till.scan("Apple"), True)

    # --- deals ---

    def test_a_deal_at_exactly_its_quantity(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        for _ in range(3):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 130)

    def test_below_the_deal_quantity_is_unit_priced(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        for _ in range(2):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 100)

    def test_the_leftover_after_a_deal(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        for _ in range(4):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 180)

    def test_the_deal_applies_more_than_once(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        for _ in range(7):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 310)

    def test_two_items_with_different_deals(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        self.till.set_price("tin", 40)
        self.till.set_deal("tin", 2, 70)
        for _ in range(4):
            self.till.scan("apple")
        for _ in range(5):
            self.till.scan("tin")
        # apples 130 + 50, tins 70 + 70 + 40
        self.assertEqual(self.till.total(), 180 + 180)

    def test_a_deal_on_one_item_leaves_the_other_alone(self):
        self.till.set_price("apple", 50)
        self.till.set_price("tin", 40)
        self.till.set_deal("apple", 2, 90)
        for _ in range(2):
            self.till.scan("apple")
            self.till.scan("tin")
        self.assertEqual(self.till.total(), 90 + 80)

    def test_replacing_a_deal(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        self.till.set_deal("apple", 2, 95)
        for _ in range(4):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 190)

    def test_a_deal_for_an_unpriced_sku_is_refused(self):
        self.assertIs(self.till.set_deal("ghost", 3, 100), False)
        self.till.set_price("ghost", 50)
        for _ in range(3):
            self.till.scan("ghost")
        self.assertEqual(self.till.total(), 150)

    def test_a_deal_quantity_below_two_is_refused(self):
        self.till.set_price("apple", 50)
        self.assertIs(self.till.set_deal("apple", 1, 30), False)
        self.till.scan("apple")
        self.assertEqual(self.till.total(), 50)

    def test_a_deal_quantity_of_zero_is_refused(self):
        """Also the one that divides by zero if it gets through."""
        self.till.set_price("apple", 50)
        self.assertIs(self.till.set_deal("apple", 0, 30), False)
        self.till.scan("apple")
        self.assertEqual(self.till.total(), 50)

    def test_a_free_deal_is_refused(self):
        self.till.set_price("apple", 50)
        self.assertIs(self.till.set_deal("apple", 3, 0), False)
        for _ in range(3):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 150)

    # --- prices that move ---

    def test_a_new_price_applies_to_what_is_already_in_the_basket(self):
        """The basket holds what was scanned, not what it cost at the time."""
        self.till.set_price("apple", 50)
        for _ in range(2):
            self.till.scan("apple")
        self.till.set_price("apple", 60)
        self.assertEqual(self.till.total(), 120)

    def test_a_new_price_with_a_deal_still_standing(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        for _ in range(4):
            self.till.scan("apple")
        self.till.set_price("apple", 60)
        self.assertEqual(self.till.total(), 190)

    def test_a_deal_set_after_scanning_still_applies(self):
        self.till.set_price("apple", 50)
        for _ in range(3):
            self.till.scan("apple")
        self.till.set_deal("apple", 3, 130)
        self.assertEqual(self.till.total(), 130)

    # --- refusals leave nothing behind ---

    def test_a_price_of_zero_is_refused(self):
        self.assertIs(self.till.set_price("apple", 0), False)
        self.assertIs(self.till.scan("apple"), False)

    def test_a_negative_price_is_refused(self):
        self.assertIs(self.till.set_price("apple", -10), False)
        self.assertIs(self.till.scan("apple"), False)

    def test_a_fractional_price_is_refused(self):
        self.assertIs(self.till.set_price("apple", 50.5), False)
        self.assertIs(self.till.scan("apple"), False)

    def test_an_empty_sku_is_refused(self):
        self.assertIs(self.till.set_price("", 50), False)
        self.assertIs(self.till.scan(""), False)
        self.assertEqual(self.till.total(), 0)

    def test_a_refused_price_does_not_replace_a_good_one(self):
        self.till.set_price("apple", 50)
        self.till.set_price("apple", 0)
        self.till.scan("apple")
        self.assertEqual(self.till.total(), 50)

    # --- clearing ---

    def test_clear_empties_the_basket(self):
        self.till.set_price("apple", 50)
        self.till.scan("apple")
        self.till.clear()
        self.assertEqual(self.till.total(), 0)

    def test_clear_keeps_prices_and_deals(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        self.till.scan("apple")
        self.till.clear()
        for _ in range(3):
            self.till.scan("apple")
        self.assertEqual(self.till.total(), 130)

    def test_total_can_be_asked_repeatedly_without_changing_anything(self):
        self.till.set_price("apple", 50)
        self.till.scan("apple")
        self.assertEqual(self.till.total(), 50)
        self.assertEqual(self.till.total(), 50)
        self.assertEqual(self.till.total(), 50)

    # --- scale ---

    def test_a_large_basket(self):
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 3, 130)
        for _ in range(100000):
            self.till.scan("apple")
        # 33333 lots of three at 130, one left at 50
        self.assertEqual(self.till.total(), 33333 * 130 + 50)

    def test_total_after_every_scan_stays_quick(self):
        """A till that re-walks the basket each time is quadratic here."""
        self.till.set_price("apple", 50)
        self.till.set_deal("apple", 2, 90)
        running = 0
        for _ in range(20000):
            self.till.scan("apple")
            running = self.till.total()
        self.assertEqual(running, 10000 * 90)

    def test_many_skus(self):
        for index in range(1000):
            self.till.set_price("sku-%d" % index, index + 1)
            self.till.scan("sku-%d" % index)
        self.assertEqual(self.till.total(), sum(range(1, 1001)))


if __name__ == "__main__":
    unittest.main()
