# Level 3: transfers

Everything from levels 1 and 2 must keep working. Money can now move directly
between accounts.

## `transfer(source, target, amount)`

Move `amount` from `source` to `target`. Returns `True` if it happened, `False`
if it did not.

It is refused when:

- either account does not exist,
- `source` and `target` are the same account,
- `amount` is not positive, or
- `source` does not hold enough.

A refused transfer changes nothing at all.

## Volume

A successful transfer counts as movement for **both** accounts, so each of their
volumes goes up by `amount`. This matters for `top_accounts`.

## Example

```python
ledger = Ledger()
ledger.create_account("alice")
ledger.create_account("bob")
ledger.deposit("alice", 500)          # alice: balance 500, volume 500

ledger.transfer("alice", "bob", 200)  # True
ledger.balance("alice")               # 300
ledger.balance("bob")                 # 200
ledger.volume("alice")                # 700
ledger.volume("bob")                  # 200

ledger.transfer("alice", "bob", 9999) # False, not enough
ledger.transfer("alice", "alice", 10) # False, same account
ledger.transfer("alice", "ghost", 10) # False, no such account
```
