# Level 2: reporting

Everything from level 1 must keep working. Add three read-only methods.

## `parcel_count()`

How many parcels are currently stored.

## `lockers_in_use()`

A sorted list of the lockers currently holding a parcel. A locker that was used
and then emptied is not in use.

## `busiest_locker()`

The locker that has taken the most parcels over the lifetime of the system,
counting every successful `store` including ones later retrieved. Refused stores
do not count.

If two lockers tie, return whichever id sorts first. If nothing has ever been
stored, return `None`.

## Example

```python
system = LockerSystem()
system.store("p1", "B")
system.store("p2", "A")
system.parcel_count()      # 2
system.lockers_in_use()    # ["A", "B"]

system.retrieve("p1")
system.parcel_count()      # 1
system.lockers_in_use()    # ["A"]
system.busiest_locker()    # "A", tied at one each, and "A" sorts first

system.store("p3", "B")
system.store("p4", "C")
system.busiest_locker()    # "B", it has taken two
```
