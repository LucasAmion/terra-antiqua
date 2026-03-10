# Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
# Full copyright notice in file: terra_antiqua.py

from PyQt5 import QtWidgets, QtCore
from ..core.dependency_checker import DependencyInstallThread


class TaInstallDependenciesDialog(QtWidgets.QDialog):
    """Dialog that asks the user to install Python dependencies, with a progress bar."""

    install_finished = QtCore.pyqtSignal(bool)  # True on success, False on failure

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terra Antiqua - Install Dependencies")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self._success = False
        self._install_thread = None
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Icon + message
        msg_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(
            self.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxInformation)
        )
        msg_layout.addWidget(icon_label, alignment=QtCore.Qt.AlignTop)

        self.message_label = QtWidgets.QLabel(
            "Terra Antiqua requires additional Python packages to run.\n\n"
            "The following packages and their dependencies will be installed in QGIS built-in python environment:\n"
            "- appdirs\n"
            "- gplately\n"
            "- plate-model-manager\n"
            "- paleo-age-grids\n\n"
            "Warning: There might be version conflicts with packages installed by other plugins, proceed at your own risk.\n"
        )
        self.message_label.setWordWrap(True)
        msg_layout.addWidget(self.message_label, 1)
        layout.addLayout(msg_layout)

        layout.addSpacing(10)

        # Progress bar (hidden initially)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label (hidden initially)
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        self.install_button = QtWidgets.QPushButton("Install")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        btn_layout.addWidget(self.install_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        # Connections
        self.install_button.clicked.connect(self._start_install)
        self.cancel_button.clicked.connect(self.reject)

    def _start_install(self):
        self.install_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("Preparing installation...")

        self._install_thread = DependencyInstallThread(self)
        self._install_thread.progress.connect(self._on_progress)
        self._install_thread.status.connect(self._on_status)
        self._install_thread.finished_ok.connect(self._on_success)
        self._install_thread.failed.connect(self._on_failure)
        self._install_thread.start()

    def _on_progress(self, value):
        _ = value

    def _on_status(self, text):
        self.status_label.setText(text)

    def _on_success(self):
        self._success = True
        self.status_label.setText("All dependencies installed successfully!")
        self.progress_bar.setVisible(False)
        self.install_button.setVisible(False)
        self.cancel_button.setText("Continue")
        self.cancel_button.setEnabled(True)
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)

    def _on_failure(self, error_msg):
        self._success = False
        self.status_label.setText("Installation failed. See details below.")
        self.progress_bar.setVisible(False)

        # Show error in a text box
        error_box = QtWidgets.QTextEdit()
        error_box.setPlainText(error_msg)
        error_box.setReadOnly(True)
        error_box.setMaximumHeight(120)
        self.layout().insertWidget(self.layout().count() - 1, error_box)

        self.install_button.setText("Retry")
        self.install_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def was_successful(self):
        return self._success
