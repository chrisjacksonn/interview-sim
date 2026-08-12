# Level 2: reporting

Everything from level 1 must keep working.

An intent that has been captured has a **captured amount**. Nothing captures
anything yet at this level, so these start at zero and stay there; they become
interesting once level 4 arrives.

## `captured_total(merchant)`

The total captured across all of that merchant's intents. Zero for a merchant
with no intents, and zero for one whose intents have not captured.

## `count_by_status()`

A dictionary mapping each status to how many intents currently hold it.
Statuses with no intents are absent. An empty system gives an empty dictionary.

## Example

```python
system = PaymentSystem()
a = system.create_intent("k1", "acme", 500, "usd")
b = system.create_intent("k2", "acme", 300, "usd")
system.create_intent("k3", "globex", 100, "usd")

system.confirm(a)
system.count_by_status()      # {"confirming": 1, "created": 2}
system.captured_total("acme") # 0, nothing has captured
system.captured_total("nobody")  # 0
```
