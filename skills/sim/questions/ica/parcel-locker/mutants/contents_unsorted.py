"""Reference solution for Parcel Locker, all four levels.

Never copied into a session workspace.

Written the way a candidate who reached level 4 would end up: the internal model
is locker -> {parcel: expiry}, which is what level 4's multi-parcel lockers
force. Levels 1 to 3 are the same code with capacity fixed at one.
"""


class LockerSystem:
    def __init__(self):
        # locker_id -> {parcel_id: expires_at or None}
        self._contents = {}
        # parcel_id -> locker_id, so lookups do not scan
        self._where = {}
        # locker_id -> how many parcels it has ever taken
        self._stores = {}
        # locker_id -> capacity. Absent means the default of one.
        self._capacity = {}

    # -- level 1 ----------------------------------------------------------

    def store(self, parcel_id, locker_id, expires_at=None):
        if parcel_id in self._where:
            return False
        contents = self._contents.setdefault(locker_id, {})
        if len(contents) >= self._capacity.get(locker_id, 1):
            return False
        contents[parcel_id] = expires_at
        self._where[parcel_id] = locker_id
        self._stores[locker_id] = self._stores.get(locker_id, 0) + 1
        return True

    def retrieve(self, parcel_id):
        locker_id = self._where.pop(parcel_id, None)
        if locker_id is None:
            return None
        self._contents[locker_id].pop(parcel_id, None)
        return locker_id

    def locate(self, parcel_id):
        return self._where.get(parcel_id)

    # -- level 2 ----------------------------------------------------------

    def parcel_count(self):
        return len(self._where)

    def lockers_in_use(self):
        return sorted(locker for locker, held in self._contents.items() if held)

    def busiest_locker(self):
        if not self._stores:
            return None
        most = max(self._stores.values())
        return min(locker for locker, count in self._stores.items() if count == most)

    # -- level 3 ----------------------------------------------------------

    def purge(self, now):
        expired = []
        for parcel_id, locker_id in self._where.items():
            deadline = self._contents[locker_id].get(parcel_id)
            if deadline is not None and deadline <= now:
                expired.append(parcel_id)
        for parcel_id in expired:
            self.retrieve(parcel_id)
        return len(expired)

    def expires_at(self, parcel_id):
        locker_id = self._where.get(parcel_id)
        if locker_id is None:
            return None
        return self._contents[locker_id].get(parcel_id)

    # -- level 4 ----------------------------------------------------------

    def set_capacity(self, locker_id, capacity):
        if capacity < 1:
            return False
        if len(self._contents.get(locker_id, {})) > capacity:
            return False
        self._capacity[locker_id] = capacity
        return True

    def capacity(self, locker_id):
        return self._capacity.get(locker_id, 1)

    def contents(self, locker_id):
        return list(self._contents.get(locker_id, {}))
