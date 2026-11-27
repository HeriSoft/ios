"""Hộp thoại Doctor: kiểm tra công cụ trên Windows (chạy nền), hiển thị hướng dẫn cài & trạng thái BLOCKED."""
from __future__ import annotations

from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app_builder.core.i18n import tr
from app_builder.services import doctor
from app_builder.ui.theme import current_palette
from app_builder.ui.widgets import label, run_in_background


class DoctorDialog(QDialog):
    def __init__(self, tool_paths: dict[str, str], workspace_dir: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("doctor.title"))
        self.resize(1000, 620)
        self.tool_paths = tool_paths
        self.workspace_dir = workspace_dir
        self.checks: list[doctor.ToolCheck] = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.addWidget(label(tr("doctor.title"), "H2"))
        lay.addWidget(label(tr("doctor.sub"), "Muted", wrap=True))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr("doctor.c_status"), tr("doctor.c_tool"), tr("doctor.c_version"),
                                              tr("doctor.c_detail"), tr("doctor.c_hint")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.table, 1)
        self.blocked = label("", "Muted", wrap=True)
        lay.addWidget(self.blocked)
        row = QHBoxLayout()
        self.btn_copy = QPushButton(tr("doctor.copy"))
        self.btn_copy.clicked.connect(self._copy)
        self.btn_run = QPushButton(tr("doctor.rerun"))
        self.btn_run.clicked.connect(self.run)
        close = QPushButton(tr("common.close"))
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        row.addWidget(self.btn_copy)
        row.addStretch(1)
        row.addWidget(self.btn_run)
        row.addWidget(close)
        lay.addLayout(row)
        self.run()

    def run(self) -> None:
        self.btn_run.setEnabled(False)
        self.blocked.setText(tr("doctor.running"))
        tp, wd = dict(self.tool_paths), self.workspace_dir
        run_in_background(lambda: doctor.run_doctor(tp, wd), self._show, self._fail)

    def _fail(self, msg: str) -> None:
        self.btn_run.setEnabled(True)
        self.blocked.setText(msg)

    def _show(self, checks: list[doctor.ToolCheck]) -> None:
        self.checks = checks
        self.btn_run.setEnabled(True)
        p = current_palette()
        colors = {doctor.OK: p.ok, doctor.WARN: p.warn, doctor.MISSING: p.danger, doctor.INFO: p.muted}
        names = {doctor.OK: "OK", doctor.WARN: tr("doctor.warn"), doctor.MISSING: tr("doctor.missing"), doctor.INFO: "Info"}
        self.table.setRowCount(len(checks))
        for i, c in enumerate(checks):
            st = QTableWidgetItem("● " + names.get(c.status, c.status))
            st.setForeground(QColor(colors.get(c.status, p.text)))
            self.table.setItem(i, 0, st)
            self.table.setItem(i, 1, QTableWidgetItem(c.name))
            self.table.setItem(i, 2, QTableWidgetItem(c.version))
            detail = "\n".join(x for x in (c.detail, c.path) if x)
            self.table.setItem(i, 3, QTableWidgetItem(detail))
            self.table.setItem(i, 4, QTableWidgetItem(c.hint if c.status != doctor.OK else ""))
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(1)
        self.table.resizeColumnToContents(2)
        self.table.resizeRowsToContents()
        blocked = doctor.blocked_features(checks)
        if blocked:
            self.blocked.setText(tr("doctor.blocked") + "  " +
                                 " · ".join(f"{f} ({', '.join(t)})" for f, t in blocked.items()))
        else:
            self.blocked.setText(tr("doctor.all_ok"))

    def _copy(self) -> None:
        QGuiApplication.clipboard().setText(doctor.format_report(self.checks))
