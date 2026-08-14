#!/usr/bin/env bash
# Build a throwaway project to record the posting demo inside.
#
# The point of the demo is that a sitting lands next to the work you already
# have open, so it has to be recorded inside something that looks like real
# work rather than an empty directory. This makes that something, and turns on
# auto mode locally so the recording is not interrupted by permission prompts.
#
#   tools/demo-project.sh              # builds /tmp/checkout-service
#   tools/demo-project.sh ~/somewhere  # or wherever you like
#
# Nothing here touches your real settings: the auto-mode file is written inside
# the throwaway directory and dies with it.

set -euo pipefail

TARGET="${1:-/tmp/checkout-service}"

rm -rf "$TARGET"
mkdir -p "$TARGET/src" "$TARGET/.claude"

cat > "$TARGET/README.md" <<'EOF'
# checkout-service

Order totals, discounts and tax for the storefront.
EOF

cat > "$TARGET/src/pricing.py" <<'EOF'
"""Line-item pricing for a basket."""


def subtotal(lines):
    return sum(line["price"] * line["quantity"] for line in lines)


def with_tax(amount, rate):
    return round(amount * (1 + rate), 2)
EOF

cat > "$TARGET/src/basket.py" <<'EOF'
"""The basket a customer is filling."""

from pricing import subtotal


class Basket:
    def __init__(self):
        self.lines = []

    def add(self, sku, price, quantity=1):
        self.lines.append({"sku": sku, "price": price, "quantity": quantity})

    def total(self):
        return subtotal(self.lines)
EOF

# Auto mode, scoped to this directory only. A timed sitting stops being timed
# if it pauses to ask permission every time the proctor reads a file.
cat > "$TARGET/.claude/settings.json" <<'EOF'
{
  "permissions": {
    "defaultMode": "auto"
  }
}
EOF

# A git repo, so the session's self-ignoring .gitignore is doing something
# visible rather than being a detail nobody can see.
if command -v git >/dev/null 2>&1; then
    git -C "$TARGET" init --quiet
    git -C "$TARGET" add -A
    git -C "$TARGET" -c user.email=demo@example.com -c user.name=demo \
        commit --quiet -m "checkout service"
fi

echo "Ready: $TARGET"
echo
echo "Next:"
echo "  1. Open $TARGET in your editor and open its integrated terminal."
echo "  2. Run: claude"
echo "  3. Start recording, then paste the skill command and a posting URL."
echo
echo "Auto mode is on for this directory only, so nothing will interrupt the take."
