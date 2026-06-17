"""Runtime feature flags.

Compact builds disable the embedded Qt WebEngine browser by default to keep
the one-file executable size down. Set MYSQL_RUNNER_EMBEDDED_BROWSER=1 to
re-enable in-app browser tabs.
"""

from __future__ import annotations

import os


def embedded_browser_enabled() -> bool:
    value = os.getenv("MYSQL_RUNNER_EMBEDDED_BROWSER", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}
