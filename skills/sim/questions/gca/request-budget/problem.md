# Request Budget

An API gateway has to stop any one client from flooding it. You are writing the
part that decides, for each incoming request, whether it is inside that client's
budget.

Build a class `RateLimiter`.

## The API

```python
RateLimiter(limit, window)
```

At most `limit` requests are allowed for any one client in any `window` seconds.
`limit` is an integer of at least 1. `window` is a positive number of seconds.

```python
allow(key, at) -> bool
```

A request from client `key` arrives at time `at`, in seconds. Return `True` if it
is inside the budget, and `False` if it is not.

An allowed request counts against the budget for `window` seconds. A refused
request does not count against anything: being turned away must not make the
next request more likely to be turned away too.

```python
count(key, at) -> int
```

How many allowed requests for `key` are still inside the budget at time `at`.
Zero for a client that has never been seen.

## The window

The window is the half-open interval `(at - window, at]`.

A request recorded at exactly `at - window` has expired and no longer counts. One
recorded a moment after it still does.

So with `limit=2, window=10`, requests at times 0 and 5 fill the budget. A
request at 9 is refused, because 0 and 5 are both still inside `(-1, 9]`. A
request at 10 is allowed, because the one at 0 has expired: only 5 remains inside
`(0, 10]`.

## Examples

```python
limiter = RateLimiter(2, 10)
limiter.allow("a", 0)      # True
limiter.allow("a", 5)      # True
limiter.allow("a", 9)      # False, budget is full
limiter.count("a", 9)      # 2
limiter.allow("a", 10)     # True, the request at 0 has expired
limiter.count("a", 10)     # 2, the ones at 5 and 10
```

```python
limiter = RateLimiter(1, 60)
limiter.allow("alice", 0)      # True
limiter.allow("bob", 0)        # True, clients are independent
limiter.allow("alice", 30)     # False
limiter.allow("alice", 60)     # True
```

## Constraints

- `at` never goes backwards: calls arrive in non-decreasing time order.
- `at` may repeat. Several requests can share a timestamp.
- Times may be negative, and may be floats.
- `key` is a non-empty string. An empty key is not a client: refuse it, count it
  as nothing, and do not raise.
- Up to 200,000 calls, across up to 10,000 clients. A solution that rescans a
  client's whole history on every call will be too slow.
- `RateLimiter(0, 10)` and `RateLimiter(2, 0)` are not valid. Raise `ValueError`.
