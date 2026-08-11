# Level 1: accounts and money

Build a `Ledger` class. Amounts are whole numbers of cents and are always
positive; anything else is rejected.

## `create_account(account_id)`

Open an account with a balance of `0`. Returns `True`, or `False` if an account
with that id already exists.

## `deposit(account_id, amount)`

Add money. Returns the **new balance**, or `None` if the account does not exist
or `amount` is not positive.

## `withdraw(account_id, amount)`

Take money out. Returns the **new balance**, or `None` if the account does not
exist, `amount` is not positive, or the account does not hold enough. An account
may never go negative.

## `balance(account_id)`

The current balance, or `None` if there is no such account.

## Example

```python
ledger = Ledger()
ledger.create_account("alice")     # True
ledger.create_account("alice")     # False, already open

ledger.deposit("alice", 500)       # 500
ledger.withdraw("alice", 200)      # 300
ledger.withdraw("alice", 1000)     # None, not enough
ledger.balance("alice")            # 300

ledger.deposit("bob", 100)         # None, no such account
ledger.balance("bob")              # None
```

## Notes

- Account ids are non-empty, case-sensitive strings.
- A balance of exactly `0` is fine. Withdrawing the full balance is allowed.
