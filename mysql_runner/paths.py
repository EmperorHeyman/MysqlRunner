"""Application paths (per-user AppData)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "MySQLRunner"


def resource_path(name: str) -> Path:
    """Return the path to a bundled resource.

    Works both in development and inside a PyInstaller build, where data files
    are unpacked to ``sys._MEIPASS``.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / name
    # Project root (two levels up from this file: mysql_runner/paths.py).
    return Path(__file__).resolve().parent.parent / name


def app_data_dir() -> Path:
    """Return the per-user application data directory, creating it if needed."""
    base = os.environ.get("APPDATA")
    if base:
        root = Path(base)
    else:
        root = Path.home() / ".config"
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def vault_path() -> Path:
    """Path to the encrypted key vault metadata file."""
    return app_data_dir() / "vault.json"


def servers_path() -> Path:
    """Path to the encrypted server profiles file."""
    return app_data_dir() / "servers.enc"


def settings_path() -> Path:
    """Path to the (plain JSON) UI settings file."""
    return app_data_dir() / "settings.json"
