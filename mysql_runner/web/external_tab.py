"""Fallback tab that opens phpMyAdmin in the system browser."""

from __future__ import annotations

import webbrowser

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from mysql_runner.storage.models import ServerProfile


class ExternalLaunchTab(QWidget):
    """Minimal tab content for compact builds without Qt WebEngine."""

    status_message = pyqtSignal(str)

    def __init__(self, profile: ServerProfile) -> None:
        super().__init__()
        self.server_profile = profile
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        text = QLabel(
            "Compact build mode is active.\n"
            "This connection opens in your default browser."
        )
        text.setWordWrap(True)
        layout.addWidget(text)

        open_btn = QPushButton("Open phpMyAdmin in browser")
        open_btn.clicked.connect(self.open_in_browser)
        layout.addWidget(open_btn)
        layout.addStretch(1)

    def open_in_browser(self) -> None:
        webbrowser.open(self.server_profile.url)
        self.status_message.emit("Opened in default browser")
