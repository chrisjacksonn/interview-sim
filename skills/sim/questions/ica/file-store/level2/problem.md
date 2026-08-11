# Level 2: sizes across the store

Everything from level 1 must keep working.

## `total_size()`

The total size of every file currently stored. Zero when the store is empty.

## `largest(count)`

The names of the `count` biggest files, largest first. Ties are broken by name,
alphabetically first. Returns fewer than `count` if there are not enough files,
and an empty list if `count` is zero or negative.

## Example

```python
store = FileStore()
store.add("a.txt", 300)
store.add("b.txt", 100)
store.add("c.txt", 300)

store.total_size()      # 700
store.largest(2)        # ["a.txt", "c.txt"], tied at 300 so name order decides
store.largest(10)       # ["a.txt", "c.txt", "b.txt"]
store.largest(0)        # []

store.delete("a.txt")
store.total_size()      # 400
```
