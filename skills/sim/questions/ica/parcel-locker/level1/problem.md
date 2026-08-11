# Level 1: storing and retrieving

Build a `LockerSystem` class. At this level every locker holds exactly one
parcel.

## `store(parcel_id, locker_id)`

Put a parcel into a locker. Returns `True` if it went in, `False` if it did not.

It does not go in when:

- that locker already holds a parcel, or
- a parcel with that id is already somewhere in the system.

## `retrieve(parcel_id)`

Take a parcel out. Returns the id of the locker it came from, or `None` if no
such parcel is stored. Once retrieved, the locker is free again and the parcel id
can be reused.

## `locate(parcel_id)`

Returns the locker holding that parcel without removing it, or `None`.

## Example

```python
system = LockerSystem()

system.store("p1", "A")        # True
system.store("p2", "A")        # False, locker A is taken
system.store("p1", "B")        # False, parcel p1 already exists
system.locate("p1")            # "A"

system.retrieve("p1")          # "A"
system.locate("p1")            # None
system.store("p2", "A")        # True, A is free now
system.retrieve("nope")        # None
```

## Notes

- Locker ids and parcel ids are non-empty strings, case-sensitive.
- There is no fixed set of lockers. Any id you are given is a real locker.
