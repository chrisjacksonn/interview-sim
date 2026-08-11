"""Reference solution for Ledger, all four levels.

Never copied into a session workspace.

Balance and volume are tracked side by side from the start, which is what makes
level 4's merge a matter of adding two numbers and dropping an id rather than
replaying a history nobody kept.
"""


class Ledger:
    def __init__(self):
        self._balance = {}
        self._volume = {}

    # -- level 1 ----------------------------------------------------------

    def create_account(self, account_id):
        if account_id in self._balance:
            return False
        self._balance[account_id] = 0
        self._volume[account_id] = 0
        return True

    def deposit(self, account_id, amount):
        if account_id not in self._balance or amount <= 0:
            return None
        self._balance[account_id] += amount
        self._volume[account_id] += amount
        return self._balance[account_id]

    def withdraw(self, account_id, amount):
        if account_id not in self._balance or amount <= 0:
            return None
        if self._balance[account_id] < amount:
            return None
        self._balance[account_id] -= amount
        self._volume[account_id] += amount
        return self._balance[account_id]

    def balance(self, account_id):
        return self._balance.get(account_id)

    # -- level 2 ----------------------------------------------------------

    def volume(self, account_id):
        return self._volume.get(account_id)

    def top_accounts(self, count):
        if count <= 0:
            return []
        ranked = sorted(self._volume.items(), key=lambda pair: (-pair[1], pair[0]))
        return [account_id for account_id, _ in ranked[:count]]

    # -- level 3 ----------------------------------------------------------

    def transfer(self, source, target, amount):
        if source not in self._balance or target not in self._balance:
            return False
        if amount <= 0 or self._balance[source] < amount:
            return False
        self._balance[source] -= amount
        self._balance[target] += amount
        self._volume[source] += amount
        self._volume[target] += amount
        return True

    # -- level 4 ----------------------------------------------------------

    def merge_accounts(self, source, target):
        if source == target:
            return False
        if source not in self._balance or target not in self._balance:
            return False
        self._balance[target] += self._balance[source]
        self._volume[target] += self._volume[source]
        del self._balance[source]
        del self._volume[source]
        return True
