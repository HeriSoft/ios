"""Panel dưới: Terminal | Problems | Build logs | Git | AI Usage | Tasks."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from app_builder.agent.budget import BudgetManager
from app_builder.core.database import Database
from app_builder.core.i18n import tr
from app_builder.ui.usage_panel import UsagePanel
from app_builder.ui.widgets import MilestoneNotice

MAX_CONSOLE_BLOCKS = 5000


class BottomPanel(QTabWidget):
    def __init__(self, db: Database, budget: BudgetManager | None = None) -> None:
        super().__init__()
        self.db = db
        self.setDocumentMode(True)
        term = QWidget()
        tl = QVBoxLayout(term)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)
        self.console = QPlainTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(MAX_CONSOLE_BLOCKS)
        tl.addWidget(self.console, 1)
        row = QHBoxLayout()
        row.setContentsMargins(6, 4, 6, 4)
        row.addStretch(1)
        self.btn_stop = QPushButton(tr("bottom.stop"))
        self.btn_stop.setEnabled(False)
        clear = QPushButton(tr("bottom.clear"))
        clear.clicked.connect(self.console.clear)
        row.addWidget(self.btn_stop)
        row.addWidget(clear)
        tl.addLayout(row)
        self.addTab(term, tr("bottom.terminal"))
        for key, ms, detail in (("bottom.problems", "M4", "bottom.problems_notice"),
                                ("bottom.build", "M6", "bottom.build_notice"),
                                ("bottom.git", "M5", "bottom.git_notice")):
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(12, 10, 12, 10)
            v.addWidget(MilestoneNotice(tr(key), ms, tr(detail)))
            v.addStretch(1)
            self.addTab(w, tr(key))
        self.usage = UsagePanel(budget or BudgetManager(db))
        self.addTab(self.usage, tr("bottom.usage"))
        self.tasks = QTableWidget(0, 5)
        self.tasks.setHorizontalHeaderLabels([tr("bottom.t_kind"), tr("bottom.t_status"), tr("bottom.t_cmd"),
                                              tr("bottom.t_start"), tr("bottom.t_end")])
        self.tasks.horizontalHeader().setStretchLastSection(True)
        self.tasks.verticalHeader().setVisible(False)
        self.tasks.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.addTab(self.tasks, tr("bottom.tasks"))

    def append(self, text: str) -> None:
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.insertPlainText(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def refresh_tasks(self, project_id: int | None) -> None:
        rows = self.db.query("SELECT * FROM jobs WHERE project_id IS ? ORDER BY created_at DESC LIMIT 50", (project_id,))
        self.tasks.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, key in enumerate(("kind", "status", "detail", "started_at", "finished_at")):
                self.tasks.setItem(i, j, QTableWidgetItem(r[key] or ""))
        self.tasks.resizeColumnsToContents()
