# Level 3: refunds

Everything from levels 1 and 2 must keep working.

Money can be given back, but only money that was actually taken, and never more
than once for the same request.

## `refund(key, intent_id, amount)`

Refund `amount` from a captured intent. Returns the amount refunded, or `None`
if it was refused.

`key` is an idempotency key, as with `create_intent`. **Calling this twice with
the same key refunds once and returns the same amount both times.** A retried
refund request is one refund.

It is refused when:

- there is no such intent, `key` is empty, or `amount` is not positive
- the intent has not captured
- the refund would take the total refunded above the captured amount

## `refunded_total(intent_id)`

How much has been refunded from that intent, or `None` if there is no such
intent.

## Note

Nothing captures until level 4, so at this level every refund is refused for a
lack of captured funds. The rules above are still the rules, and the tests hold
you to them.

## Example

```python
system = PaymentSystem()
intent = system.create_intent("k1", "acme", 500, "usd")

system.refund("r1", intent, 100)     # None, nothing was captured
system.refunded_total(intent)        # 0
system.refunded_total("nope")        # None
```
