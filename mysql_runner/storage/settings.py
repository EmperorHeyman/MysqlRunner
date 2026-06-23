"""Plain-JSON UI settings (non-sensitive preferences only).

These preferences do not contain credentials, so they are stored unencrypted:
dark-mode toggle, sidebar visibility, the idle auto-lock timeout, and the
master-password prompt policy.
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
    # Prompt for the master password on every app launch (ignore the keyring
    # cache at startup). The keyring is still used for in-session re-unlocks.
    ask_password_on_start: bool = False
    # Keep the password cached after locking so unlocking never prompts again.
    remember_password: bool = False
    # "Stay logged in": unlock once, then never auto-lock and never re-prompt.
    # This is a convenience preset that overrides the three options above while
    # enabled; a real master password is still kept and the vault stays
    # encrypted. See the effective_* helpers below.
    stay_logged_in: bool = False

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
            ask_password_on_start=bool(data.get("ask_password_on_start", False)),
            remember_password=bool(data.get("remember_password", False)),
            stay_logged_in=bool(data.get("stay_logged_in", False)),
        )

    # ----- effective behaviour -------------------------------------------
    # "Stay logged in" takes precedence over the granular options so the app
    # only ever has to consult these three helpers.
    def effective_idle_lock_minutes(self) -> int:
        """Idle timeout in minutes; 0 (never) while staying logged in."""
        return 0 if self.stay_logged_in else self.idle_lock_minutes

    def keep_password_cached(self) -> bool:
        """Whether the cached key should survive a lock (no re-prompt)."""
        return self.stay_logged_in or self.remember_password

    def prompt_on_start(self) -> bool:
        """Whether to ignore the keyring and ask for the password at launch."""
        return self.ask_password_on_start and not self.stay_logged_in

    def save(self) -> None:
        settings_path().write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )
