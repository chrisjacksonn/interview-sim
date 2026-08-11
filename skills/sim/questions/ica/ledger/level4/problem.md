# Level 4: merging accounts

Everything from levels 1 to 3 must keep working. Two accounts can now be
combined.

Until now every account id was permanent. That is no longer true.

## `merge_accounts(source, target)`

Fold `source` into `target`. Returns `True` if it happened, `False` if it did
not.

After a successful merge:

- `target`'s balance is the sum of the two balances.
- `target`'s volume is the sum of the two volumes. A merge is not itself
  movement, so nothing extra is added.
- `source` **no longer exists**. Its balance and volume are `None`, it cannot be
  deposited into or withdrawn from, it does not appear in `top_accounts`, and it
  cannot be the source or target of a transfer.
- The id `source` is free again, so `create_account(source)` succeeds and gives
  a brand new empty account.

It is refused when either account does not exist, or when `source` and `target`
are the same.

## Example

```python
ledger = Ledger()
ledger.create_account("old")
ledger.create_account("new")
ledger.deposit("old", 300)            # old: balance 300, volume 300
ledger.deposit("new", 100)            # new: balance 100, volume 100

ledger.merge_accounts("old", "new")   # True
ledger.balance("new")                 # 400
ledger.volume("new")                  # 400
ledger.balance("old")                 # None
ledger.deposit("old", 50)             # None

ledger.create_account("old")          # True, the id is free again
ledger.balance("old")                 # 0
```
