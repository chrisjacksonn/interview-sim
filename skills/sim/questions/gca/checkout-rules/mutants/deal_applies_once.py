"""Deliberately wrong: applies a deal at most once, so seven apples is one deal and four singles

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

class Checkout:
    def __init__(self):
        self._prices = {}
        self._deals = {}
        self._counts = {}

    @staticmethod
    def _whole(value):
        return isinstance(value, int) and not isinstance(value, bool) and value > 0

    def set_price(self, sku, price):
        if not isinstance(sku, str) or not sku or not self._whole(price):
            return False
        self._prices[sku] = price
        return True

    def set_deal(self, sku, quantity, price):
        if not isinstance(sku, str) or sku not in self._prices:
            return False
        if not self._whole(quantity) or quantity < 2 or not self._whole(price):
            return False
        self._deals[sku] = (quantity, price)
        return True

    def scan(self, sku):
        if not isinstance(sku, str) or sku not in self._prices:
            return False
        self._counts[sku] = self._counts.get(sku, 0) + 1
        return True

    def clear(self):
        self._counts = {}

    def total(self):
        running = 0
        for sku, count in self._counts.items():
            price = self._prices[sku]
            deal = self._deals.get(sku)
            if deal is None:
                running += count * price
                continue
            quantity, deal_price = deal
            if count >= quantity:
                running += deal_price + (count - quantity) * price
            else:
                running += count * price
        return running
