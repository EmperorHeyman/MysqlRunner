"""Add/edit dialog for a server profile."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
)

from mysql_runner.storage.models import AuthType, Environment, ServerProfile

_AUTH_LABELS = {
    AuthType.AUTO: "Auto-detect",
    AuthType.COOKIE: "phpMyAdmin login form",
    AuthType.HTTP_BASIC: "HTTP Basic Auth",
}

_ENV_LABELS = {
    Environment.NONE: "None",
    Environment.DEV: "Development",
    Environment.STAGING: "Staging",
    Environment.PROD: "Production",
}


class ServerDialog(QDialog):
    """Collects/edits the fields of a :class:`ServerProfile`."""

    def __init__(self, parent=None, profile: ServerProfile | None = None) -> None:
        super().__init__(parent)
        self._profile = profile
        self.setWindowTitle("Edit Server" if profile else "Add Server")
        self.setModal(True)
        self.setMinimumWidth(460)

        form = QFormLayout(self)

        self._label = QLineEdit()
        self._url = QLineEdit()
        self._url.setPlaceholderText("https://example.com/phpmyadmin/")
        self._username = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        self._auth = QComboBox()
        for auth_type, text in _AUTH_LABELS.items():
            self._auth.addItem(text, auth_type)

        self._group = QLineEdit()
        self._group.setPlaceholderText("e.g. Production, Client A (optional)")

        self._environment = QComboBox()
        for env, text in _ENV_LABELS.items():
            self._environment.addItem(text, env)

        self._startup = QPlainTextEdit()
        self._startup.setPlaceholderText(
            "Optional SQL run automatically after login, e.g. SET NAMES utf8;"
        )
        self._startup.setFixedHeight(80)

        form.addRow("Display name:", self._label)
        form.addRow("URL:", self._url)
        form.addRow("Username:", self._username)
        form.addRow("Password:", self._password)
        form.addRow("Authentication:", self._auth)
        form.addRow("Group:", self._group)
        form.addRow("Environment:", self._environment)
        form.addRow("Startup SQL:", self._startup)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        if profile:
            self._load(profile)

    def _load(self, profile: ServerProfile) -> None:
        self._label.setText(profile.label)
        self._url.setText(profile.url)
        self._username.setText(profile.username)
        self._password.setText(profile.password)
        index = self._auth.findData(profile.auth_type)
        if index >= 0:
            self._auth.setCurrentIndex(index)
        self._group.setText(profile.group)
        env_index = self._environment.findData(profile.environment)
        if env_index >= 0:
            self._environment.setCurrentIndex(env_index)
        self._startup.setPlainText(profile.startup_script)

    def _on_accept(self) -> None:
        if not self._label.text().strip():
            QMessageBox.warning(self, "Missing name", "Please enter a display name.")
            return
        url = self._url.text().strip()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(
                self, "Invalid URL", "URL must start with http:// or https://"
            )
            return
        self.accept()

    def result_profile(self) -> ServerProfile:
        """Return a profile built from the field values."""
        kwargs = {
            "label": self._label.text().strip(),
            "url": self._url.text().strip(),
            "username": self._username.text(),
            "password": self._password.text(),
            "auth_type": self._auth.currentData(),
            "group": self._group.text().strip(),
            "environment": self._environment.currentData(),
            "startup_script": self._startup.toPlainText(),
        }
        if self._profile:
            return ServerProfile(id=self._profile.id, **kwargs)
        return ServerProfile(**kwargs)
