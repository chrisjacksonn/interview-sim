# Level 3: expiry

Parcels can now be left with a deadline. Everything from levels 1 and 2 must keep
working, including calls to `store` that pass no deadline at all.

## `store(parcel_id, locker_id, expires_at=None)`

Same as before, with an optional third argument. `expires_at` is an integer time.
`None` means the parcel never expires.

Existing calls of the form `store("p1", "A")` must keep behaving exactly as they
did.

## `expires_at(parcel_id)`

The deadline for a stored parcel, or `None` if it has no deadline or is not
stored.

## `purge(now)`

Remove every stored parcel whose deadline has been reached, meaning
`expires_at <= now`. Returns how many were removed.

Purged parcels are gone exactly as if retrieved: their lockers free up, their ids
become reusable, and the counts from level 2 reflect the removal. A purge does
not change any locker's lifetime store count.

## Example

```python
system = LockerSystem()
system.store("p1", "A", 10)
system.store("p2", "B", 20)
system.store("p3", "C")          # no deadline

system.purge(5)                  # 0, nothing has expired
system.purge(10)                 # 1, p1 is due exactly now
system.locate("p1")              # None
system.parcel_count()            # 2

system.purge(100)                # 1, p2 goes, p3 never expires
system.lockers_in_use()          # ["C"]
```
