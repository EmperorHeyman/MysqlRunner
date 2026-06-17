"""Main application window: server sidebar + tabbed browser views."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mysql_runner.storage.models import Environment, ServerProfile
from mysql_runner.storage.portable import PortableError, export_profiles, import_profiles
from mysql_runner.storage.settings import Settings
from mysql_runner.storage.store import ServerStore
from mysql_runner.ui.server_dialog import ServerDialog
from mysql_runner.web.browser_tab import BrowserTab

_NO_SELECTION = "No selection"
_UNGROUPED = "Ungrouped"

_ENV_COLORS = {
    Environment.PROD: QColor("#e53935"),
    Environment.STAGING: QColor("#fb8c00"),
}


class MainWindow(QMainWindow):
    """Sidebar list of saved phpMyAdmin servers plus a tab per open session."""

    def __init__(
        self,
        store: ServerStore,
        settings: Settings | None = None,
        on_lock=None,
    ) -> None:
        super().__init__()
        self._store = store
        self._settings = settings or Settings()
        self._on_lock = on_lock
        # Reference counts for engine profiles shared between cloned tabs.
        self._profile_refs: dict[object, int] = {}
        self.setWindowTitle("MySQL Runner")
        self.resize(1200, 800)

        self._build_ui()
        self._build_menus()
        self._build_shortcuts()
        self._refresh_server_list()
        self._apply_settings()

    # ----- UI construction ----------------------------------------------
    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Sidebar.
        self._sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(6, 6, 6, 6)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search servers…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_filter)
        sidebar_layout.addWidget(self._search)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemDoubleClicked.connect(self._on_item_activated)
        sidebar_layout.addWidget(self._tree)

        button_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        add_btn.clicked.connect(self._on_add)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)
        button_row.addWidget(add_btn)
        button_row.addWidget(edit_btn)
        button_row.addWidget(delete_btn)
        sidebar_layout.addLayout(button_row)

        open_btn = QPushButton("Connect")
        open_btn.clicked.connect(self._on_connect)
        sidebar_layout.addWidget(open_btn)

        lock_btn = QPushButton("Lock")
        lock_btn.clicked.connect(self._on_lock_clicked)
        sidebar_layout.addWidget(lock_btn)

        # Tabs.
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setMovable(True)
        self._tabs.tabCloseRequested.connect(self._on_tab_close)

        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 920])

        self.setCentralWidget(splitter)
        self.statusBar().showMessage("Ready")

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        export_action = QAction("&Export connections…", self)
        export_action.triggered.connect(self._on_export)
        import_action = QAction("&Import connections…", self)
        import_action.triggered.connect(self._on_import)
        lock_action = QAction("&Lock now", self)
        lock_action.triggered.connect(self._on_lock_clicked)
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(export_action)
        file_menu.addAction(import_action)
        file_menu.addSeparator()
        file_menu.addAction(lock_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        view_menu = menubar.addMenu("&View")
        self._sidebar_action = QAction("Toggle &sidebar", self)
        self._sidebar_action.setCheckable(True)
        self._sidebar_action.setChecked(self._settings.sidebar_visible)
        self._sidebar_action.setShortcut("Ctrl+B")
        self._sidebar_action.triggered.connect(self._toggle_sidebar)
        self._dark_action = QAction("&Dark mode", self)
        self._dark_action.setCheckable(True)
        self._dark_action.setChecked(self._settings.dark_mode)
        self._dark_action.setShortcut("Ctrl+Shift+D")
        self._dark_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(self._sidebar_action)
        view_menu.addAction(self._dark_action)

        tab_menu = menubar.addMenu("&Tabs")
        clone_action = QAction("&Clone current tab", self)
        clone_action.setShortcut("Ctrl+D")
        clone_action.triggered.connect(self._clone_current_tab)
        close_action = QAction("C&lose current tab", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self._close_current_tab)
        tab_menu.addAction(clone_action)
        tab_menu.addAction(close_action)

    def _build_shortcuts(self) -> None:
        # Cycle tabs.
        nxt = QShortcut(QKeySequence("Ctrl+Tab"), self)
        nxt.activated.connect(lambda: self._cycle_tab(1))
        prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev.activated.connect(lambda: self._cycle_tab(-1))
        # Jump to tab 1-9.
        for i in range(1, 10):
            sc = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            sc.activated.connect(lambda idx=i - 1: self._goto_tab(idx))

    def _apply_settings(self) -> None:
        self._sidebar.setVisible(self._settings.sidebar_visible)

    # ----- server list ---------------------------------------------------
    def _refresh_server_list(self) -> None:
        self._tree.clear()
        groups: dict[str, QTreeWidgetItem] = {}
        for profile in self._store.all():
            group_name = profile.group.strip() or _UNGROUPED
            parent = groups.get(group_name)
            if parent is None:
                parent = QTreeWidgetItem([group_name])
                parent.setFirstColumnSpanned(True)
                parent.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._tree.addTopLevelItem(parent)
                parent.setExpanded(True)
                groups[group_name] = parent
            item = QTreeWidgetItem([profile.label])
            item.setData(0, Qt.ItemDataRole.UserRole, profile.id)
            item.setToolTip(0, profile.url)
            color = _ENV_COLORS.get(profile.environment)
            if color is not None:
                item.setForeground(0, color)
            parent.addChild(item)
        self._apply_filter(self._search.text())

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self._tree.topLevelItemCount()):
            group = self._tree.topLevelItem(i)
            visible_children = 0
            for j in range(group.childCount()):
                child = group.child(j)
                match = needle in child.text(0).lower()
                child.setHidden(bool(needle) and not match)
                if not child.isHidden():
                    visible_children += 1
            group.setHidden(bool(needle) and visible_children == 0)

    def _selected_profile(self) -> ServerProfile | None:
        item = self._tree.currentItem()
        if item is None:
            return None
        profile_id = item.data(0, Qt.ItemDataRole.UserRole)
        if profile_id is None:
            return None
        return self._store.get(profile_id)

    # ----- CRUD actions --------------------------------------------------
    def _on_add(self) -> None:
        dialog = ServerDialog(self)
        if dialog.exec():
            self._store.add(dialog.result_profile())
            self._refresh_server_list()

    def _on_edit(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            QMessageBox.information(self, _NO_SELECTION, "Select a server to edit.")
            return
        dialog = ServerDialog(self, profile=profile)
        if dialog.exec():
            self._store.update(dialog.result_profile())
            self._refresh_server_list()

    def _on_delete(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            QMessageBox.information(self, _NO_SELECTION, "Select a server to delete.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete server",
            f"Delete '{profile.label}'? This cannot be undone.",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._store.delete(profile.id)
            self._refresh_server_list()

    # ----- export / import ----------------------------------------------
    def _on_export(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        profiles = self._store.all()
        if not profiles:
            QMessageBox.information(self, "Nothing to export", "No servers saved yet.")
            return
        passphrase, ok = QInputDialog.getText(
            self,
            "Export passphrase",
            "Choose a passphrase to protect the exported file:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not passphrase:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export connections", "connections.mrx", "MySQL Runner Export (*.mrx)"
        )
        if not path:
            return
        try:
            export_profiles(profiles, passphrase, path)
        except PortableError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(
            self, "Export complete", f"Exported {len(profiles)} server(s)."
        )

    def _on_import(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self, "Import connections", "", "MySQL Runner Export (*.mrx);;All files (*)"
        )
        if not path:
            return
        passphrase, ok = QInputDialog.getText(
            self,
            "Import passphrase",
            "Enter the passphrase for this file:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        try:
            profiles = import_profiles(path, passphrase)
        except PortableError as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return
        count = self._store.add_many(profiles)
        self._refresh_server_list()
        QMessageBox.information(self, "Import complete", f"Imported {count} server(s).")

    # ----- connecting ----------------------------------------------------
    def _on_item_activated(self, _item: QTreeWidgetItem) -> None:
        self._on_connect()

    def _on_connect(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            QMessageBox.information(self, _NO_SELECTION, "Select a server to connect.")
            return
        self._open_tab(profile)

    def _open_tab(self, profile: ServerProfile) -> None:
        tab = BrowserTab(profile, dark_mode=self._settings.dark_mode)
        self._register_profile(tab.engine_profile)
        index = self._tabs.addTab(tab, profile.label)
        self._style_tab(index, profile)
        self._tabs.setCurrentIndex(index)
        tab.status_message.connect(self._on_tab_status)
        tab.title_changed.connect(lambda title, t=tab: self._update_tab_title(t, title))

    def _clone_current_tab(self) -> None:
        tab = self._tabs.currentWidget()
        if not isinstance(tab, BrowserTab):
            return
        source_profile = tab.server_profile
        clone = BrowserTab(
            source_profile,
            dark_mode=self._settings.dark_mode,
            shared_profile=tab.engine_profile,
        )
        self._register_profile(clone.engine_profile)
        index = self._tabs.addTab(clone, f"{source_profile.label} (clone)")
        self._style_tab(index, source_profile)
        self._tabs.setCurrentIndex(index)
        clone.status_message.connect(self._on_tab_status)
        clone.title_changed.connect(lambda title, t=clone: self._update_tab_title(t, title))

    def _style_tab(self, index: int, profile: ServerProfile) -> None:
        color = _ENV_COLORS.get(profile.environment)
        if color is not None:
            self._tabs.tabBar().setTabTextColor(index, color)
            self._tabs.setTabText(index, f"● {self._tabs.tabText(index)}")
            if profile.environment == Environment.PROD:
                self._tabs.setTabToolTip(index, "PRODUCTION — be careful!")

    def _update_tab_title(self, tab: BrowserTab, title: str) -> None:
        index = self._tabs.indexOf(tab)
        if index >= 0:
            short = title if len(title) <= 24 else title[:21] + "…"
            prefix = "● " if tab.server_profile.environment in _ENV_COLORS else ""
            self._tabs.setTabText(index, prefix + short)
            self._tabs.setTabToolTip(index, title)

    def _on_tab_status(self, message: str) -> None:
        if message:
            self.statusBar().showMessage(message, 4000)

    # ----- tab navigation ------------------------------------------------
    def _cycle_tab(self, delta: int) -> None:
        count = self._tabs.count()
        if count == 0:
            return
        self._tabs.setCurrentIndex((self._tabs.currentIndex() + delta) % count)

    def _goto_tab(self, index: int) -> None:
        if 0 <= index < self._tabs.count():
            self._tabs.setCurrentIndex(index)

    def _close_current_tab(self) -> None:
        index = self._tabs.currentIndex()
        if index >= 0:
            self._on_tab_close(index)

    def _on_tab_close(self, index: int) -> None:
        widget = self._tabs.widget(index)
        self._tabs.removeTab(index)
        if isinstance(widget, BrowserTab):
            profile = widget.engine_profile
            widget.cleanup()
            self._release_profile(profile)
        if widget is not None:
            widget.deleteLater()

    # ----- engine profile lifetime --------------------------------------
    def _register_profile(self, profile) -> None:
        self._profile_refs[profile] = self._profile_refs.get(profile, 0) + 1

    def _release_profile(self, profile) -> None:
        remaining = self._profile_refs.get(profile, 0) - 1
        if remaining <= 0:
            self._profile_refs.pop(profile, None)
            # Drop the in-memory profile (and its cookies) now that the last
            # tab using it is gone.
            profile.deleteLater()
        else:
            self._profile_refs[profile] = remaining

    # ----- view toggles --------------------------------------------------
    def _toggle_sidebar(self) -> None:
        visible = not self._sidebar.isVisible()
        self._sidebar.setVisible(visible)
        self._sidebar_action.setChecked(visible)
        self._settings.sidebar_visible = visible
        self._settings.save()

    def _toggle_dark_mode(self) -> None:
        enabled = self._dark_action.isChecked()
        self._settings.dark_mode = enabled
        self._settings.save()
        for i in range(self._tabs.count()):
            widget = self._tabs.widget(i)
            if isinstance(widget, BrowserTab):
                widget.set_dark_mode(enabled)

    # ----- lock ----------------------------------------------------------
    def _on_lock_clicked(self) -> None:
        if self._on_lock is not None:
            self._on_lock()
