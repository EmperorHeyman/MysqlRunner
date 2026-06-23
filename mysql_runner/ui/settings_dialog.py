"""Application settings dialog (appearance + password/locking options)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from mysql_runner.storage.settings import Settings

# (label, minutes) — 0 means "never auto-lock".
_LOCK_CHOICES = [
    ("Never", 0),
    ("After 1 minute", 1),
    ("After 5 minutes", 5),
    ("After 15 minutes", 15),
    ("After 30 minutes", 30),
    ("After 1 hour", 60),
]


class SettingsDialog(QDialog):
    """Edits user preferences. Read the getters after :meth:`exec` returns truthy."""

    def __init__(self, settings: Settings, parent=None, *, on_change_password=None) -> None:
        super().__init__(parent)
        self._on_change_password = on_change_password
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)

        # ----- Appearance -------------------------------------------------
        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self._dark = QCheckBox("Dark mode")
        self._dark.setChecked(settings.dark_mode)
        self._sidebar = QCheckBox("Show server sidebar")
        self._sidebar.setChecked(settings.sidebar_visible)
        appearance_form.addRow(self._dark)
        appearance_form.addRow(self._sidebar)
        layout.addWidget(appearance)

        # ----- Password & locking ----------------------------------------
        security = QGroupBox("Password && locking")
        sec_form = QFormLayout(security)

        # The headline option: unlock once and never get pestered again.
        self._stay = QCheckBox("Stay logged in (unlock once, never ask again)")
        self._stay.setChecked(settings.stay_logged_in)
        self._stay.toggled.connect(self._sync_stay_logged_in)
        sec_form.addRow(self._stay)

        stay_hint = QLabel(
            "Keeps you signed in until you click “Lock” or quit. Your "
            "connections stay encrypted — this just stops the app from "
            "re-asking for the master password."
        )
        stay_hint.setWordWrap(True)
        stay_hint.setStyleSheet("color: gray;")
        sec_form.addRow(stay_hint)

        self._lock = QComboBox()
        for label, minutes in _LOCK_CHOICES:
            self._lock.addItem(label, minutes)
        self._select_lock(settings.idle_lock_minutes)
        sec_form.addRow("Auto-lock when idle:", self._lock)

        self._ask_start = QCheckBox("Ask for master password when the app starts")
        self._ask_start.setChecked(settings.ask_password_on_start)
        sec_form.addRow(self._ask_start)

        self._remember = QCheckBox("Remember password (don't ask again after locking)")
        self._remember.setChecked(settings.remember_password)
        sec_form.addRow(self._remember)

        change_btn = QPushButton("Change master password…")
        change_btn.clicked.connect(self._on_change_clicked)
        sec_form.addRow(change_btn)

        layout.addWidget(security)

        # Reflect the initial "stay logged in" state on the granular controls.
        self._sync_stay_logged_in(self._stay.isChecked())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ----- helpers --------------------------------------------------------
    def _select_lock(self, minutes: int) -> None:
        index = self._lock.findData(minutes)
        if index < 0:
            label = "Never" if minutes <= 0 else f"After {minutes} minutes"
            self._lock.addItem(label, minutes)
            index = self._lock.count() - 1
        self._lock.setCurrentIndex(index)

    def _sync_stay_logged_in(self, staying: bool) -> None:
        """Disable the granular options while "stay logged in" overrides them."""
        # When staying logged in, the auto-lock / ask-on-start / remember
        # controls have no effect, so grey them out to make that obvious.
        self._lock.setEnabled(not staying)
        self._ask_start.setEnabled(not staying)
        self._remember.setEnabled(not staying)

    def _on_change_clicked(self) -> None:
        if self._on_change_password is not None:
            self._on_change_password(self)

    # ----- result accessors ----------------------------------------------
    def dark_mode(self) -> bool:
        return self._dark.isChecked()

    def sidebar_visible(self) -> bool:
        return self._sidebar.isChecked()

    def idle_lock_minutes(self) -> int:
        return int(self._lock.currentData())

    def ask_password_on_start(self) -> bool:
        return self._ask_start.isChecked()

    def remember_password(self) -> bool:
        return self._remember.isChecked()

    def stay_logged_in(self) -> bool:
        return self._stay.isChecked()
