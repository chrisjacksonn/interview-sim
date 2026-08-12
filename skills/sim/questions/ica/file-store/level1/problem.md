# Level 1: storing files

Build a `FileStore` class holding files by name, each with a size in bytes.

## `add(name, size)`

Store a new file. Returns `True`, or `False` if a file with that name already
exists, the name is empty, or `size` is negative. A size of `0` is a real file.

## `get(name)`

The file's size, or `None` if there is no such file.

## `delete(name)`

Remove a file and return the size it had, or `None` if there was no such file.

## Example

```python
store = FileStore()
store.add("notes.txt", 120)    # True
store.add("notes.txt", 999)    # False, already there
store.get("notes.txt")         # 120

store.delete("notes.txt")      # 120
store.get("notes.txt")         # None
store.delete("notes.txt")      # None

store.add("notes.txt", 5)      # True, the name is free again
```

## Notes

- Names are case-sensitive. An empty name is possible and must be refused.
- A negative size is possible and must be refused. Zero is a real size.
