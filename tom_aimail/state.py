"""Tiny local state for Tom AImail: which senders we have served before.

Stored as a JSON file next to the service (gitignored). Used for one
human touch: a welcome line the first time someone writes to us.
"""

from __future__ import annotations

import json
from pathlib import Path


class StateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._senders: set[str] = set()
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self._senders = {str(addr).lower() for addr in data.get("senders", [])}
            except (ValueError, AttributeError):
                self._senders = set()

    def is_new_sender(self, address: str) -> bool:
        return address.lower() not in self._senders

    def remember_sender(self, address: str) -> None:
        self._senders.add(address.lower())
        self.path.write_text(
            json.dumps({"senders": sorted(self._senders)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
