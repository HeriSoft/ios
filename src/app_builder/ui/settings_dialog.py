"""Cài đặt chung: ngôn ngữ, theme, thư mục workspace, đường dẫn công cụ, dữ liệu local."""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from app_builder.core.config import AppSettings, data_dir
from app_builder.core.database import Database
from app_builder.core.i18n import tr
from app_builder.ui.widgets import label

TOOL_KEYS = [("node", "Node.js (node.exe)", False), ("git", "Git (git.exe)", False), ("gh", "GitHub CLI (gh.exe)", False),
             ("java_home", "JAVA_HOME", True), ("android_sdk", "Android SDK", True),
             ("claude", "Claude Code CLI", False), ("eas", "EAS CLI", False)]


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings.model_copy(deep=True)
        self.db = db
        self.setWindowTitle(tr("settings.title"))
        self.setMinimumWidth(680)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.addWidget(label(tr("settings.title"), "H2"))

        gen = QGroupBox(tr("settings.general"))
        f = QFormLayout(gen)
        self.lang = QComboBox()
        self.lang.addItem("Tiếng Việt", "vi")
        self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(0 if self.settings.language == "vi" else 1)
        self.theme = QComboBox()
        self.theme.addItem(tr("settings.dark"), "dark")
        self.theme.addItem(tr("settings.light"), "light")
        self.theme.setCurrentIndex(0 if self.settings.theme == "dark" else 1)
        ws_row = QHBoxLayout()
        self.ws = QLineEdit(self.settings.workspace_dir)
        b = QPushButton(tr("wiz.browse"))
        b.clicked.connect(lambda: self._pick_dir(self.ws))
        ws_row.addWidget(self.ws, 1)
        ws_row.addWidget(b)
        self.keep_history = QCheckBox(tr("settings.keep_history"))
        self.keep_history.setChecked(self.settings.keep_message_history)
        f.addRow(tr("settings.language"), self.lang)
        f.addRow(tr("settings.theme"), self.theme)
        f.addRow(tr("settings.workspace"), ws_row)
        f.addRow("", self.keep_history)
        lay.addWidget(gen)

        tools = QGroupBox(tr("settings.tools"))
        tf = QFormLayout(tools)
        self.tool_edits: dict[str, QLineEdit] = {}
        for key, name, is_dir in TOOL_KEYS:
            row = QHBoxLayout()
            e = QLineEdit(self.settings.tool_paths.get(key, ""))
            e.setPlaceholderText(tr("settings.auto_detect"))
            btn = QPushButton("…")
            btn.setFixedWidth(34)
            btn.clicked.connect(lambda _=False, e=e, d=is_dir: self._pick_dir(e) if d else self._pick_file(e))
            row.addWidget(e, 1)
            row.addWidget(btn)
            self.tool_edits[key] = e
            tf.addRow(name, row)
        lay.addWidget(tools)

        data = QGroupBox(tr("settings.data"))
        dl = QHBoxLayout(data)
        dl.addWidget(label(str(data_dir()), "Muted"), 1)
        open_btn = QPushButton(tr("settings.open_data"))
        open_btn.clicked.connect(lambda: os.startfile(str(data_dir())))  # noqa: S606
        clear_btn = QPushButton(tr("settings.clear_cache"))
        clear_btn.setObjectName("Danger")
        clear_btn.clicked.connect(self._clear_cache)
        dl.addWidget(open_btn)
        dl.addWidget(clear_btn)
        lay.addWidget(data)
        lay.addWidget(label(tr("settings.no_telemetry"), "Muted", wrap=True))

        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton(tr("common.cancel"))
        cancel.clicked.connect(self.reject)
        ok = QPushButton(tr("common.save"))
        ok.setObjectName("Primary")
        ok.clicked.connect(self._save)
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addLayout(row)

    def _pick_dir(self, e: QLineEdit) -> None:
        d = QFileDialog.getExistingDirectory(self, "", e.text())
        if d:
            e.setText(d)

    def _pick_file(self, e: QLineEdit) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "", e.text(), "Programs (*.exe *.cmd *.bat)")
        if f:
            e.setText(f)

    def _clear_cache(self) -> None:
        if QMessageBox.question(self, tr("settings.clear_cache"), tr("settings.clear_confirm")) \
                != QMessageBox.StandardButton.Yes:
            return
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM messages")
            cur.execute("DELETE FROM conversations")
            cur.execute("DELETE FROM model_cache")
        self.db.audit("settings.cache_cleared")
        QMessageBox.information(self, tr("settings.clear_cache"), tr("settings.cleared"))

    def _save(self) -> None:
        self.settings.language = self.lang.currentData()
        self.settings.theme = self.theme.currentData()
        self.settings.workspace_dir = self.ws.text().strip() or self.settings.workspace_dir
        self.settings.keep_message_history = self.keep_history.isChecked()
        self.settings.tool_paths = {k: e.text().strip() for k, e in self.tool_edits.items() if e.text().strip()}
        self.accept()
