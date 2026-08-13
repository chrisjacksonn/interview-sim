# Checkout Rules

A till has to total a basket while the pricing team keeps changing its mind.
Prices are per unit, and some items also carry a multibuy deal: three for the
price of two, that sort of thing.

Build a class `Checkout`.

## The API

```python
Checkout()
```

Starts empty. No prices, no deals, no basket.

```python
set_price(sku, price)
```

The price of one unit of `sku`, in pence, as a whole number greater than zero.
Calling it again for the same sku replaces the old price, including for items
already scanned: the basket holds what was scanned, not what it cost at the time.

```python
set_deal(sku, quantity, price)
```

`quantity` units of `sku` together cost `price` pence, instead of `quantity`
times the unit price. `quantity` is at least 2, `price` is greater than zero.
Calling it again replaces that sku's deal. Setting a deal for an sku with no
price is refused.

```python
scan(sku) -> bool
```

Add one unit to the basket. `True` if it was added, `False` if the sku has no
price, in which case nothing is added.

```python
total() -> int
```

The basket total in pence.

```python
clear()
```

Empty the basket. Prices and deals stay.

## How deals apply

A deal applies as many times as it fits, and whatever is left over is charged at
the unit price.

With apples at 50 each and a deal of 3 for 130:

| Apples | Total |
| --- | --- |
| 2 | 100 |
| 3 | 130 |
| 4 | 180 |
| 7 | 310 |

Seven is two lots of three at 130, plus one at 50.

A deal is never worse than paying per unit here, and you do not need to check
for that: apply the deal whenever the quantity reaches it.

## Examples

```python
till = Checkout()
till.set_price("apple", 50)
till.set_deal("apple", 3, 130)
for _ in range(4):
    till.scan("apple")
till.total()            # 180

till.set_price("apple", 60)
till.total()            # 190, three for 130 and one at the new 60
```

```python
till = Checkout()
till.scan("ghost")      # False, no price
till.total()            # 0
```

## Constraints

- Skus are non-empty, case-sensitive strings. An empty sku is refused by
  `set_price` and by `scan`.
- Prices and deal prices are whole pence, greater than zero. `set_price` with
  zero, a negative, or a non-integer is refused and changes nothing.
- `set_deal` with a quantity below 2 is refused.
- Up to 100,000 scans across up to 1,000 skus. `total()` may be called after
  every scan, so it should not be doing work proportional to the basket each
  time it is asked, or a big basket becomes quadratic.
- Refusals return `False` where the method returns a bool, and otherwise do
  nothing at all. Nothing here raises.
