# Level 4: the processor answers back

Everything from levels 1 to 3 must keep working.

Until now an intent's status was whatever the last call set. It no longer is. The
outcome comes from an external processor, over a channel that is **at least
once**: callbacks can be duplicated, delayed, and reordered.

## `processor_callback(callback_id, intent_id, outcome, amount=None)`

Apply a processor callback. Returns `True` if it changed anything, `False` if it
did not.

`outcome` is `"captured"` or `"declined"`. `amount` is how much was actually
captured, defaulting to the intent's full amount when omitted; it is ignored for
a decline.

The rules that make this hard:

- **A duplicate callback does nothing.** The same `callback_id` seen twice is one
  event. The second returns `False` and changes nothing.
- **Capture is final.** Once an intent has captured, no later callback may change
  it, whatever it says and whatever order it arrives in. A decline that overtook
  a capture on the network must not undo the capture, and a second capture must
  not charge again.
- An empty `callback_id`, an unknown intent, or an unrecognised outcome returns
  `False`.

A captured intent has status `"captured"`; a declined one `"declined"`.

## What this changes

`captured_total` now has real numbers in it. `refund` now has something to refund
from, and its ceiling is the **captured** amount, which is not always the amount
the intent was created for: a processor may capture less.

## Example

```python
system = PaymentSystem()
intent = system.create_intent("k1", "acme", 500, "usd")
system.confirm(intent)

system.processor_callback("cb-1", intent, "captured")        # True
system.status(intent)                                        # "captured"
system.captured_total("acme")                                # 500

system.processor_callback("cb-1", intent, "captured")        # False, duplicate
system.processor_callback("cb-2", intent, "declined")        # False, capture is final
system.captured_total("acme")                                # still 500

system.refund("r1", intent, 200)                             # 200
system.refund("r1", intent, 200)                             # 200, same request
system.refunded_total(intent)                                # 200
system.refund("r2", intent, 400)                             # None, would exceed 500
```
