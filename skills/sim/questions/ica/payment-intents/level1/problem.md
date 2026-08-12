# Level 1: intents

Build a `PaymentSystem`. An **intent** is one attempt to charge one amount.

## `create_intent(key, merchant, amount, currency)`

Create an intent and return its id, a string.

`key` is an idempotency key supplied by the caller. **Calling this twice with the
same key must return the same id and must not create a second intent.** Networks
retry; the same request arriving twice is one intent, not two.

Returns `None` if `key` is empty, `merchant` is empty, `currency` is empty, or
`amount` is not positive.

A new intent has status `"created"`.

## `confirm(intent_id)`

Move an intent from `"created"` to `"confirming"`. Returns `True` if it moved,
`False` if there is no such intent or it was not in `"created"`.

## `status(intent_id)`

The intent's current status, or `None` if there is no such intent.

## Example

```python
system = PaymentSystem()
first = system.create_intent("req-1", "acme", 500, "usd")   # "pi_1"
again = system.create_intent("req-1", "acme", 500, "usd")   # "pi_1", the same
system.status(first)                                        # "created"

system.confirm(first)                                       # True
system.status(first)                                        # "confirming"
system.confirm(first)                                       # False, already moved

system.create_intent("req-2", "acme", 0, "usd")             # None
system.status("nope")                                       # None
```

## Notes

- Ids are strings you choose; they only have to be unique and stable.
- Merchant names and currencies are non-empty, case-sensitive strings.
- Amounts are integers in the smallest currency unit.
