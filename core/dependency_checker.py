# Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
# Full copyright notice in file: terra_antiqua.py

from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal


def check_dependencies():
    """Return True if the plugin's third-party dependencies are installed."""
    try:
        from .terra_antiqua import TerraAntiqua  # noqa: F401
    except ImportError:
        return False
    return True


class DependencyInstallThread(QThread):
    """Runs pip install in a background thread, emitting progress signals."""

    progress = pyqtSignal(int)          # 0-100
    status = pyqtSignal(str)            # human-readable status text
    finished_ok = pyqtSignal()          # emitted on success
    failed = pyqtSignal(str)            # emitted on failure with error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._requirements_path = Path(__file__).parent.parent / "requirements.txt"

    def run(self):
        try:
            self.status.emit("Installing dependencies...")
            self.progress.emit(5)

            from pip._internal.cli.main import main as pip_main

            self.progress.emit(10)
            exit_code = pip_main([
                "install", "--no-deps", "-U",
                "-r", str(self._requirements_path),
            ])

            self.progress.emit(90)

            if exit_code != 0:
                self.failed.emit(
                    f"pip install failed with exit code {exit_code}.\n"
                    "Please check the QGIS Python console for details."
                )
                return

            self.progress.emit(100)
            self.status.emit("Dependencies installed successfully.")
            self.finished_ok.emit()

        except Exception as e:
            self.failed.emit(str(e))
