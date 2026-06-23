"""Application bootstrap: unlock the vault, then show the main window."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QIcon

# Import WebEngine before QApplication construction for embedded browser tabs.
from PyQt6 import QtWebEngineWidgets  # noqa: F401
from PyQt6.QtWidgets import QApplication, QMessageBox

from mysql_runner.crypto import vault as vault_mod
from mysql_runner.paths import resource_path
from mysql_runner.storage.settings import Settings
from mysql_runner.storage.store import ServerStore, StoreError
from mysql_runner.ui.idle_watcher import IdleWatcher
from mysql_runner.ui.main_window import MainWindow
from mysql_runner.ui.master_password_dialog import (
    CreateMasterPasswordDialog,
    UnlockDialog,
)


def _unlock_vault(use_keyring: bool = True) -> vault_mod.Vault | None:
    """Run the first-run / unlock flow, returning an open Vault or None.

    When ``use_keyring`` is False the cached key is ignored and the master
    password is always requested (used to honour "ask for password at start").
    """
    if not vault_mod.is_initialized():
        dialog = CreateMasterPasswordDialog()
        if not dialog.exec():
            return None
        return vault_mod.initialize(dialog.password())

    # Try the keyring cache first (unless the caller wants a password prompt).
    if use_keyring:
        vault = vault_mod.unlock_with_keyring()
        if vault is not None:
            return vault

    # Fall back to the master password (allow a few attempts).
    for _ in range(3):
        dialog = UnlockDialog()
        if not dialog.exec():
            return None
        try:
            return vault_mod.unlock_with_password(dialog.password())
        except vault_mod.InvalidMasterPassword:
            QMessageBox.warning(
                None, "Incorrect password", "That master password is incorrect."
            )
    return None


def run() -> int:
    QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("MySQL Runner")

    icon_file = resource_path("icon.ico")
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))

    # Make Windows treat this as its own app (correct taskbar icon/grouping).
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "RAPLGroup.MySQLRunner.1.0"
            )
        except Exception:
            pass

    settings = Settings.load()
    window_holder: dict[str, MainWindow] = {}
    lock_holder: dict[str, object] = {}

    # Application-wide idle watcher that auto-locks after inactivity.
    idle_watcher = IdleWatcher(settings.effective_idle_lock_minutes())
    app.installEventFilter(idle_watcher)
    idle_watcher.idle.connect(lambda: _invoke(lock_holder.get("on_lock")))

    def on_settings_changed() -> None:
        # Re-arm the idle watcher whenever the timeout preference changes.
        idle_watcher.set_timeout(settings.effective_idle_lock_minutes())

    def start_session(*, first_launch: bool = False) -> bool:
        # Honour "ask for password at start" only on the initial launch; an
        # in-session re-lock still uses the keyring (if it wasn't cleared).
        use_keyring = not (first_launch and settings.prompt_on_start())
        vault = _unlock_vault(use_keyring)
        if vault is None:
            return False
        try:
            store = ServerStore(vault)
        except StoreError as exc:
            QMessageBox.critical(None, "Vault error", str(exc))
            return False

        def on_lock() -> None:
            idle_watcher.stop()
            vault.lock()
            # Keep the cached key only when the user opted to be remembered
            # (or chose to stay logged in).
            if not settings.keep_password_cached():
                vault_mod.clear_keyring_cache()
            old = window_holder.pop("window", None)
            if old is not None:
                old.close()
            if not start_session():
                app.quit()

        window = MainWindow(
            store, settings, on_lock=on_lock, on_settings_changed=on_settings_changed
        )
        window_holder["window"] = window
        lock_holder["on_lock"] = on_lock
        window.show()
        # (Re)start the idle countdown for the new session.
        idle_watcher.set_timeout(settings.effective_idle_lock_minutes())
        return True

    if not start_session(first_launch=True):
        return 0

    return app.exec()


def _invoke(callback) -> None:
    if callable(callback):
        callback()
