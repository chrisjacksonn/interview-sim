# Level 4: versions

Everything from levels 1 to 3 must keep working. A file can now be changed, and
its previous sizes are kept.

Until now a file had one size. From now on a file has a **history** of sizes,
and the most recent one is the live size that everything else reports.

## `update(name, size)`

Give an existing file a new size, keeping the old one in its history. Returns
`True`, or `False` if there is no such file or `size` is negative.

`add` still refuses a name that already exists; `update` is how a file changes.

## `revert(name)`

Drop the newest size and go back to the previous one. Returns `True`, or `False`
if there is no such file or it has only ever had one size. A file always keeps at
least one version.

## `version_count(name)`

How many sizes the file has had, counting the live one. `None` if there is no
such file. A newly added file has `1`.

## What this changes

`get`, `total_size`, `largest`, `find`, and `total_size_with_prefix` all report
the **live** size, which is the newest one. `delete` removes the file and its
whole history, and returns the live size.

## Example

```python
store = FileStore()
store.add("a.txt", 100)      # version_count 1
store.update("a.txt", 250)   # True
store.get("a.txt")           # 250
store.version_count("a.txt") # 2
store.total_size()           # 250, not 350

store.revert("a.txt")        # True
store.get("a.txt")           # 100
store.version_count("a.txt") # 1
store.revert("a.txt")        # False, nothing left to go back to

store.update("ghost", 5)     # False
```
