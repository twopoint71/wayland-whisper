import json
import os
import subprocess
import sys

from pathlib import Path

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError as exc:
    raise SystemExit(
        "PyQt6 is required for the tray app. Install it with `pip install PyQt6`."
    ) from exc


def _xdg_dir(env_var, fallback_suffix):
    base = os.environ.get(env_var)
    if base:
        return Path(base)
    return Path.home() / fallback_suffix


def _state_path():
    cache_dir = _xdg_dir("XDG_CACHE_HOME", ".cache") / "wayland-whisper"
    return cache_dir / "recording.json"


def _load_state():
    try:
        with _state_path().open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _is_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _is_recording():
    state = _load_state()
    return state.get("recording") and _is_alive(state.get("pid"))


class TrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.icon_recording = self._make_icon("#e53935")
        self.icon_idle = self._make_icon("#9e9e9e")
        self.menu = QtWidgets.QMenu()
        self.status_action = self.menu.addAction("Status: idle")
        self.status_action.setEnabled(False)
        self.menu.addSeparator()
        self.toggle_action = self.menu.addAction("Toggle Recording")
        self.toggle_action.triggered.connect(self.toggle_recording)
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.app.quit)
        self.setContextMenu(self.menu)
        self.setToolTip("wayland-whisper")

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _make_icon(self, color):
        size = 22
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(color))
        radius = size * 0.4
        center = size / 2
        painter.drawEllipse(
            QtCore.QPointF(center, center),
            radius,
            radius,
        )
        painter.end()
        return QtGui.QIcon(pixmap)

    def refresh(self):
        recording = _is_recording()
        if recording:
            self.setIcon(self.icon_recording)
            self.status_action.setText("Status: recording")
            self.setToolTip("Recording active")
        else:
            self.setIcon(self.icon_idle)
            self.status_action.setText("Status: idle")
            self.setToolTip("Recording idle")

    def toggle_recording(self):
        subprocess.Popen([sys.executable, "-m", "faster_whisper.recorder", "toggle"])


def main():
    app = QtWidgets.QApplication(sys.argv)
    tray = TrayApp(app)
    tray.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
