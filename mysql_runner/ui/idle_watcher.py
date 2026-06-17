"""Global idle watcher that locks the app after a period of inactivity."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QTimer, pyqtSignal


class IdleWatcher(QObject):
    """Watches application-wide input and fires :pyattr:`idle` after a timeout.

    Install it on the :class:`QApplication` instance. Any mouse move, click,
    key press, scroll, or touch resets the countdown. When ``timeout_minutes``
    elapses with no input, the ``idle`` signal is emitted.
    """

    idle = pyqtSignal()

    _INPUT_EVENTS = {
        QEvent.Type.MouseMove,
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.KeyPress,
        QEvent.Type.Wheel,
        QEvent.Type.TouchBegin,
        QEvent.Type.TouchUpdate,
    }

    def __init__(self, timeout_minutes: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.idle.emit)
        self.set_timeout(timeout_minutes)

    def set_timeout(self, minutes: int) -> None:
        """Set the idle timeout. ``0`` disables auto-lock."""
        self._minutes = max(0, int(minutes))
        if self._minutes <= 0:
            self._timer.stop()
        else:
            self._timer.start(self._minutes * 60_000)

    def reset(self) -> None:
        if self._minutes > 0:
            self._timer.start(self._minutes * 60_000)

    def stop(self) -> None:
        self._timer.stop()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in self._INPUT_EVENTS:
            self.reset()
        return super().eventFilter(obj, event)
