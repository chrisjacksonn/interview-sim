# Level 3: prefixes

Everything from levels 1 and 2 must keep working. Files are organised by name
prefix, the way directories work.

## `find(prefix)`

Every stored file name starting with `prefix`, sorted alphabetically. An empty
prefix matches every file. Returns an empty list when nothing matches.

## `total_size_with_prefix(prefix)`

The total size of the files that `find(prefix)` would return. Zero when nothing
matches.

## Example

```python
store = FileStore()
store.add("docs/a.txt", 100)
store.add("docs/b.txt", 200)
store.add("images/c.png", 50)

store.find("docs/")                  # ["docs/a.txt", "docs/b.txt"]
store.find("")                       # all three, sorted
store.find("nothing")                # []

store.total_size_with_prefix("docs/")  # 300
store.total_size_with_prefix("")       # 350
```

A prefix is a plain string prefix. It is not a path component, so `"doc"`
matches `"docs/a.txt"`.
