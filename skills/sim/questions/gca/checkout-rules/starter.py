"""Checkout Rules.

Read problem.md for the full statement.
"""


class Checkout:
    """A till: prices, multibuy deals, and a basket."""

    def __init__(self):
        raise NotImplementedError

    def set_price(self, sku, price):
        """Price of one unit, in whole pence. False if refused."""
        raise NotImplementedError

    def set_deal(self, sku, quantity, price):
        """`quantity` units for `price` pence. False if refused."""
        raise NotImplementedError

    def scan(self, sku):
        """Add one unit to the basket. False if the sku has no price."""
        raise NotImplementedError

    def total(self):
        """The basket total in pence."""
        raise NotImplementedError

    def clear(self):
        """Empty the basket. Prices and deals stay."""
        raise NotImplementedError
