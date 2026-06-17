"""Plain-JSON UI settings (non-sensitive preferences only).

These preferences do not contain credentials, so they are stored unencrypted:
dark-mode toggle, sidebar visibility, and the idle auto-lock timeout.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from mysql_runner.paths import settings_path


@dataclass
class Settings:
    """User-interface preferences."""

    dark_mode: bool = False
    sidebar_visible: bool = True
    idle_lock_minutes: int = 15  # 0 disables auto-lock.

    @classmethod
    def load(cls) -> "Settings":
        path = settings_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return cls()
        return cls(
            dark_mode=bool(data.get("dark_mode", False)),
            sidebar_visible=bool(data.get("sidebar_visible", True)),
            idle_lock_minutes=int(data.get("idle_lock_minutes", 15)),
        )

    def save(self) -> None:
        settings_path().write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )
