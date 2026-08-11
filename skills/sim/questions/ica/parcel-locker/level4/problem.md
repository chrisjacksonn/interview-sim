# Level 4: bigger lockers

Some lockers can hold more than one parcel. Everything from levels 1 to 3 must
keep working unchanged.

Until now a locker held exactly one parcel. That is now the *default*, not the
rule.

## `set_capacity(locker_id, capacity)`

Set how many parcels a locker can hold. Returns `True` if the change was made,
`False` if it was refused.

It is refused when:

- `capacity` is less than 1, or
- the locker currently holds more parcels than the new capacity.

A locker never mentioned to `set_capacity` has a capacity of 1, which is what
makes every earlier level still behave the same way.

## `capacity(locker_id)`

The locker's capacity. `1` for any locker never configured.

## `contents(locker_id)`

A sorted list of the parcel ids currently in that locker, empty if there are
none.

## What this changes

`store` now refuses only when the locker is **full**, meaning it already holds
`capacity` parcels. Duplicate parcel ids are still refused as always.

`lockers_in_use` still means lockers holding at least one parcel. `busiest_locker`
still counts every successful store.

## Example

```python
system = LockerSystem()
system.set_capacity("A", 3)      # True
system.capacity("A")             # 3
system.capacity("B")             # 1, never configured

system.store("p1", "A")          # True
system.store("p2", "A")          # True, room for three
system.store("p3", "A")          # True
system.store("p4", "A")          # False, full
system.contents("A")             # ["p1", "p2", "p3"]

system.retrieve("p2")
system.contents("A")             # ["p1", "p3"]
system.store("p4", "A")          # True, there is room again

system.set_capacity("A", 1)      # False, it holds three
system.set_capacity("A", 0)      # False, capacity must be at least 1
```
