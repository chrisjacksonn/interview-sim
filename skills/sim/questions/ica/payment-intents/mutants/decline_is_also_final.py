"""Reference solution for Payment Intents, all four levels.

Never copied into a session workspace.

The shape level 4 forces: an intent is not a status field that confirm writes,
it is a record whose status is decided by the processor callbacks it has seen.
Levels 1 to 3 are the same code with exactly one callback per intent.
"""


class PaymentSystem:
    def __init__(self):
        # intent id -> record
        self._intents = {}
        # idempotency key -> intent id
        self._keys = {}
        self._next = 1
        # callback ids already applied, so a replay changes nothing
        self._seen_callbacks = set()

    # -- level 1 ----------------------------------------------------------

    def create_intent(self, key, merchant, amount, currency):
        if not key or not merchant or amount <= 0 or not currency:
            return None
        if key in self._keys:
            return self._keys[key]

        intent_id = "pi_%d" % (self._next,)
        self._next += 1
        self._intents[intent_id] = {
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "status": "created",
            "captured": 0,
            "refunded": 0,
            "refund_keys": {},
        }
        self._keys[key] = intent_id
        return intent_id

    def confirm(self, intent_id):
        record = self._intents.get(intent_id)
        if record is None or record["status"] != "created":
            return False
        record["status"] = "confirming"
        return True

    def status(self, intent_id):
        record = self._intents.get(intent_id)
        return record["status"] if record else None

    # -- level 2 ----------------------------------------------------------

    def captured_total(self, merchant):
        return sum(
            record["captured"]
            for record in self._intents.values()
            if record["merchant"] == merchant
        )

    def count_by_status(self):
        counts = {}
        for record in self._intents.values():
            counts[record["status"]] = counts.get(record["status"], 0) + 1
        return counts

    # -- level 3 ----------------------------------------------------------

    def refund(self, key, intent_id, amount):
        record = self._intents.get(intent_id)
        if record is None or not key or amount <= 0:
            return None
        if key in record["refund_keys"]:
            return record["refund_keys"][key]
        if record["status"] != "captured":
            return None
        if record["refunded"] + amount > record["captured"]:
            return None
        record["refunded"] += amount
        record["refund_keys"][key] = amount
        return amount

    def refunded_total(self, intent_id):
        record = self._intents.get(intent_id)
        return record["refunded"] if record else None

    # -- level 4 ----------------------------------------------------------

    def processor_callback(self, callback_id, intent_id, outcome, amount=None):
        if not callback_id or callback_id in self._seen_callbacks:
            return False
        record = self._intents.get(intent_id)
        if record is None:
            return False
        if outcome not in ("captured", "declined"):
            return False

        self._seen_callbacks.add(callback_id)

        # A capture is final. A later declined callback for the same intent,
        # arriving out of order, must not undo it, and a second capture must
        # not charge twice.
        if record["status"] in ("captured", "declined"):
            return False
        if outcome == "declined":
            record["status"] = "declined"
            return True

        record["status"] = "captured"
        record["captured"] = record["amount"] if amount is None else amount
        return True
