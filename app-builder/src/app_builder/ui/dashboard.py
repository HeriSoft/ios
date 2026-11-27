"""Dashboard: dự án gần đây, tìm kiếm, tạo mới, import thư mục, duplicate, gỡ khỏi danh sách."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLineEdit, QMenu, QMessageBox,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from app_builder.core.i18n import tr
from app_builder.services.project_service import ProjectError, ProjectRecord, ProjectService
from app_builder.ui.widgets import badge, label


def _fmt_time(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


class ProjectCard(QFrame):
    open_clicked = Signal(int)
    menu_action = Signal(str, int)

    def __init__(self, rec: ProjectRecord) -> None:
        super().__init__()
        self.rec = rec
        self.setObjectName("Card")
        self.setMinimumHeight(170)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 12, 14)
        lay.setSpacing(6)
        top = QHBoxLayout()
        title = label(rec.name, "H2")
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        top.addWidget(title, 1)
        more = QPushButton("⋯")
        more.setObjectName("Flat")
        more.setToolTip(tr("dash.more"))
        more.clicked.connect(self._show_menu)
        top.addWidget(more)
        lay.addLayout(top)
        desc = label(rec.description or tr("dash.no_description"), "Muted", wrap=True)
        desc.setMaximumHeight(40)
        lay.addWidget(desc)
        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addWidget(badge(rec.template or "?"))
        for p in rec.platforms:
            chips.addWidget(badge("Android" if p == "android" else "iOS"))
        if not rec.exists:
            chips.addWidget(badge(tr("dash.missing_folder"), "danger"))
        elif not rec.trusted:
            chips.addWidget(badge(tr("dash.untrusted"), "warn"))
        chips.addStretch(1)
        lay.addLayout(chips)
        lay.addStretch(1)
        path = label(rec.path, "Muted")
        path.setToolTip(rec.path)
        path.setMaximumWidth(420)
        lay.addWidget(path)
        build = rec.last_build_status or tr("dash.no_build")
        lay.addWidget(label(tr("dash.opened_build", opened=_fmt_time(rec.last_opened_at), build=build), "Muted"))

    def mouseDoubleClickEvent(self, e) -> None:  # noqa: N802
        self.open_clicked.emit(self.rec.id)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.open_clicked.emit(self.rec.id)

    def _show_menu(self) -> None:
        m = QMenu(self)
        for key, text in (("open", tr("dash.open")), ("duplicate", tr("dash.duplicate")),
                          ("reveal", tr("dash.reveal")), (None, None), ("remove", tr("dash.remove"))):
            if key is None:
                m.addSeparator()
                continue
            act = m.addAction(text)
            act.setData(key)
            if key in ("open", "duplicate", "reveal") and not self.rec.exists:
                act.setEnabled(False)
        chosen = m.exec(self.cursor().pos())
        if chosen:
            self.menu_action.emit(chosen.data(), self.rec.id)


class Dashboard(QWidget):
    open_project = Signal(int)
    new_project = Signal()
    show_doctor = Signal()

    def __init__(self, projects: ProjectService) -> None:
        super().__init__()
        self.setObjectName("Root")
        self.projects = projects
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 20)
        root.setSpacing(14)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label(tr("dash.title"), "H1"))
        titles.addWidget(label(tr("dash.subtitle"), "Muted"))
        head.addLayout(titles, 1)
        self.btn_doctor = QPushButton(tr("dash.doctor"))
        self.btn_doctor.clicked.connect(self.show_doctor.emit)
        self.btn_import = QPushButton(tr("dash.import"))
        self.btn_import.clicked.connect(self._import)
        self.btn_new = QPushButton(tr("dash.new"))
        self.btn_new.setObjectName("Primary")
        self.btn_new.clicked.connect(self.new_project.emit)
        for b in (self.btn_doctor, self.btn_import, self.btn_new):
            head.addWidget(b)
        root.addLayout(head)

        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("dash.search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        root.addWidget(self.search)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(14)
        self.grid.setContentsMargins(0, 4, 0, 4)
        self.scroll_area.setWidget(self.grid_host)
        root.addWidget(self.scroll_area, 1)
        self.refresh()

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        for r in range(self.grid.rowCount()):
            self.grid.setRowStretch(r, 0)
        for c in range(self.grid.columnCount()):
            self.grid.setColumnStretch(c, 0)
        items = self.projects.list_projects(self.search.text().strip())
        if not items:
            empty = QFrame()
            empty.setObjectName("Notice")
            v = QVBoxLayout(empty)
            v.setContentsMargins(30, 30, 30, 30)
            v.addWidget(label("🚀", "H1"), 0, Qt.AlignmentFlag.AlignHCenter)
            msg = tr("dash.empty_search") if self.search.text().strip() else tr("dash.empty")
            v.addWidget(label(msg, "H2"), 0, Qt.AlignmentFlag.AlignHCenter)
            v.addWidget(label(tr("dash.empty_hint"), "Muted", wrap=True), 0, Qt.AlignmentFlag.AlignHCenter)
            self.grid.addWidget(empty, 0, 0, 1, 3)
            self.grid.setRowStretch(1, 1)
            return
        cols = 3 if self.width() > 1100 else 2
        for i, rec in enumerate(items):
            card = ProjectCard(rec)
            card.open_clicked.connect(self._open)
            card.menu_action.connect(self._menu)
            self.grid.addWidget(card, i // cols, i % cols)
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        self.grid.setRowStretch(len(items) // cols + 1, 1)

    def resizeEvent(self, e) -> None:  # noqa: N802
        super().resizeEvent(e)
        cols_now = 3 if self.width() > 1100 else 2
        if getattr(self, "_cols", None) != cols_now:
            self._cols = cols_now
            self.refresh()

    def _open(self, pid: int) -> None:
        rec = self.projects.get(pid)
        if not rec.exists:
            QMessageBox.warning(self, tr("dash.missing_folder"), tr("dash.missing_folder_msg", path=rec.path))
            return
        self.open_project.emit(pid)

    def _import(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("dash.import"))
        if not folder:
            return
        if not os.path.isfile(os.path.join(folder, "package.json")):
            if QMessageBox.question(self, tr("dash.import"), tr("dash.import_no_package")) != QMessageBox.StandardButton.Yes:
                return
        try:
            rec = self.projects.import_folder(folder)
        except ProjectError as exc:
            QMessageBox.warning(self, tr("dash.import"), str(exc))
            return
        QMessageBox.information(self, tr("dash.import"), tr("dash.import_done"))
        self.refresh()
        self.open_project.emit(rec.id)

    def _menu(self, action: str, pid: int) -> None:
        rec = self.projects.get(pid)
        if action == "open":
            self._open(pid)
        elif action == "reveal":
            os.startfile(rec.path)  # noqa: S606 - mở Explorer tới thư mục project
        elif action == "duplicate":
            name, ok = QInputDialog.getText(self, tr("dash.duplicate"), tr("dash.duplicate_name"),
                                            text=f"{rec.name} copy")
            if ok and name.strip():
                try:
                    self.projects.duplicate(pid, name.strip()[:60])
                except (ProjectError, OSError) as exc:
                    QMessageBox.warning(self, tr("dash.duplicate"), str(exc))
                self.refresh()
        elif action == "remove":
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle(tr("dash.remove"))
            box.setText(tr("dash.remove_confirm", name=rec.name))
            box.setInformativeText(tr("dash.remove_note", path=rec.path))
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            box.setDefaultButton(QMessageBox.StandardButton.Cancel)
            if box.exec() == QMessageBox.StandardButton.Yes:
                self.projects.remove_from_list(pid)
                self.refresh()
