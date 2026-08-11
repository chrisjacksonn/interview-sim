"""Reference solution for File Store, all four levels.

Never copied into a session workspace.

Files are held in one dictionary keyed by name. Level 4's versioning turns that
value into a stack of sizes, with the live file always at the top, which is why
every earlier level keeps working: they only ever read the top.
"""


class FileStore:
    def __init__(self):
        # name -> list of sizes, oldest first, the live one last
        self._versions = {}

    def _live(self, name):
        history = self._versions.get(name)
        if not history:
            return None
        return history[-1]

    # -- level 1 ----------------------------------------------------------

    def add(self, name, size):
        if not name or size < 0:
            return False
        if name in self._versions:
            return False
        self._versions[name] = [size]
        return True

    def get(self, name):
        return self._live(name)

    def delete(self, name):
        if name not in self._versions:
            return None
        size = self._versions[name][-1]
        del self._versions[name]
        return size

    # -- level 2 ----------------------------------------------------------

    def total_size(self):
        return sum(history[-1] for history in self._versions.values())

    def largest(self, count):
        if count <= 0:
            return []
        ranked = sorted(
            ((name, history[-1]) for name, history in self._versions.items()),
            key=lambda pair: (-pair[1], pair[0]),
        )
        return [name for name, _ in ranked[:count]]

    # -- level 3 ----------------------------------------------------------

    def find(self, prefix):
        return sorted(name for name in self._versions if name.startswith(prefix))

    def total_size_with_prefix(self, prefix):
        return sum(
            history[-1]
            for name, history in self._versions.items()
            if name.startswith(prefix)
        )

    # -- level 4 ----------------------------------------------------------

    def update(self, name, size):
        if name not in self._versions or size < 0:
            return False
        self._versions[name].append(size)
        return True

    def revert(self, name):
        history = self._versions.get(name)
        if not history:
            return False
        history.pop()
        return True

    def version_count(self, name):
        history = self._versions.get(name)
        if history is None:
            return None
        return len(history)
