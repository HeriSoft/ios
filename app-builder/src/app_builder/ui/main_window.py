"""Cửa sổ chính: thanh công cụ, Dashboard ↔ Workspace IDE (Project | Workspace | AI Assistant | Bottom)."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QComboBox, QLabel, QMainWindow, QMenu, QMessageBox, QSizePolicy, QSplitter, QStackedWidget,
    QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from app_builder import APP_NAME, __version__
from app_builder.agent.budget import BudgetManager
from app_builder.core.config import AppSettings, save_settings
from app_builder.core.database import Database
from app_builder.core.i18n import language, tr
from app_builder.core.permissions import TRUST_WARNING_EN, TRUST_WARNING_VI
from app_builder.core.secret_store import SecretStore
from app_builder.services.ai_connections import ConnectionManager
from app_builder.services.project_service import ProjectRecord, ProjectService
from app_builder.ui.assistant_panel import AssistantPanel
from app_builder.ui.bottom_panel import BottomPanel
from app_builder.ui.connections_dialog import ConnectionsDialog
from app_builder.ui.dashboard import Dashboard
from app_builder.ui.doctor_dialog import DoctorDialog
from app_builder.ui.editor_panel import CodeHighlighter, EditorTabs, lang_for
from app_builder.ui.preview_panel import PreviewPanel
from app_builder.ui.process_runner import ProcessRunner
from app_builder.ui.project_panel import ProjectPanel
from app_builder.ui.project_wizard import ProjectWizard
from app_builder.ui.settings_dialog import SettingsDialog
from app_builder.ui.theme import apply_theme
from app_builder.ui.usage_dialog import UsageDialog, usd
from app_builder.ui.widgets import MilestoneNotice, badge, label, set_badge_kind

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings, db: Database, projects: ProjectService,
                 secrets: SecretStore | None = None) -> None:
        super().__init__()
        self.settings = settings
        self.db = db
        self.projects = projects
        self.secrets = secrets or SecretStore()
        self.connections = ConnectionManager(db, self.secrets)
        self.budget = BudgetManager(db)
        self.current: ProjectRecord | None = None
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.setMinimumSize(1280, 720)
        self.runner = ProcessRunner(db, self)

        self._build_toolbars()
        self.stack = QStackedWidget()
        self.dashboard = Dashboard(projects)
        self.dashboard.open_project.connect(self.open_project)
        self.dashboard.new_project.connect(self.new_project)
        self.dashboard.show_doctor.connect(self.show_doctor)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self._build_workspace())
        self.setCentralWidget(self.stack)

        self.runner.output.connect(self.bottom.append)
        self.runner.started.connect(lambda _: self._runner_state(True))
        self.runner.finished.connect(self._runner_finished)
        self.bottom.btn_stop.clicked.connect(self.runner.stop)

        sb = self.statusBar()
        self.status_path = QLabel("")
        self.status_trust = badge("")
        self.status_trust.setVisible(False)
        sb.addWidget(self.status_path, 1)
        sb.addPermanentWidget(self.status_trust)
        sb.addPermanentWidget(QLabel(f"Expo SDK {projects.templates.sdk().get('expo_sdk', '?')}  "))

        if settings.window_geometry:
            self.restoreGeometry(QByteArray.fromBase64(settings.window_geometry.encode()))
        else:
            self.resize(1440, 860)
        self.show_dashboard()
        self._refresh_ai_status()

    # ---- UI construction -------------------------------------------------------
    def _build_toolbars(self) -> None:
        top = QToolBar("main")
        top.setMovable(False)
        top.setObjectName("TopBar")
        self.addToolBar(top)
        top.addWidget(label("◆ App Builder AI", "Logo"))
        top.addSeparator()
        top.addWidget(QLabel(tr("tb.project") + " "))
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(220)
        self.project_combo.activated.connect(self._project_combo_changed)
        top.addWidget(self.project_combo)
        top.addWidget(QLabel("  " + tr("tb.platform") + " "))
        self.platform_combo = QComboBox()
        for key, text in (("android", "Android"), ("ios", "iOS"), ("both", tr("tb.both"))):
            self.platform_combo.addItem(text, key)
        self.platform_combo.setToolTip(tr("tb.platform_tip"))
        top.addWidget(self.platform_combo)
        top.addWidget(QLabel("  " + tr("tb.ai") + " "))
        self.ai_badge = badge("")
        self.ai_badge.setToolTip(tr("conn.title"))
        top.addWidget(self.ai_badge)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top.addWidget(spacer)
        self.budget_badge = badge("")
        self.budget_badge.setToolTip(tr("usage.title"))
        top.addWidget(self.budget_badge)

        self.addToolBarBreak()
        acts = QToolBar("actions")
        acts.setMovable(False)
        acts.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(acts)

        def act(text: str, slot=None, shortcut=None, enabled=True, tip: str | None = None) -> QAction:
            a = QAction(text, self)
            if slot:
                a.triggered.connect(slot)
            if shortcut:
                a.setShortcut(shortcut)
            a.setEnabled(enabled)
            if tip:
                a.setToolTip(tip)
            acts.addAction(a)
            return a

        act("⌂ " + tr("tb.home"), self.show_dashboard)
        act("＋ " + tr("tb.new"), self.new_project, QKeySequence.StandardKey.New)
        act("📂 " + tr("tb.open"), self.dashboard_import, QKeySequence.StandardKey.Open)
        self.a_save = act("💾 " + tr("tb.save"), self._save)
        self.a_undo = act("↶ " + tr("tb.undo"), lambda: self._editor_call("undo"))
        self.a_redo = act("↷ " + tr("tb.redo"), lambda: self._editor_call("redo"))
        acts.addSeparator()
        self.a_run = act("▶ " + tr("tb.run"), enabled=False, tip=tr("common.planned", milestone="M4"))
        self.a_stop = act("■ " + tr("tb.stop"), self.runner.stop, enabled=False, tip=tr("tb.stop_tip"))
        acts.addSeparator()
        act("↑ GitHub", enabled=False, tip=tr("common.planned", milestone="M5"))
        export_btn = QToolButton()
        export_btn.setText("⇩ " + tr("tb.export") + " ▾")
        export_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(export_btn)
        for text, ms in ((tr("tb.export_zip"), "M5"), ("APK Debug", "M6"), ("APK Release", "M6"), ("AAB", "M6"),
                         ("iOS (EAS)", "M7")):
            a = menu.addAction(f"{text}   ({tr('common.planned', milestone=ms)})")
            a.setEnabled(False)
        export_btn.setMenu(menu)
        acts.addWidget(export_btn)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        acts.addWidget(spacer)
        act("🔌 " + tr("tb.ai_connect"), self.show_connections)
        act("$ " + tr("tb.ai_usage"), self.show_usage)
        act("◐ " + tr("tb.theme"), self._toggle_theme)
        act("🩺 Doctor", self.show_doctor)
        act("⚙ " + tr("tb.settings"), self.show_settings)
        self._editor_actions = [self.a_save, self.a_undo, self.a_redo]

    def _build_workspace(self) -> QWidget:
        self.project_panel = ProjectPanel()
        self.project_panel.open_file.connect(self._open_file)
        self.project_panel.request_install.connect(self.install_dependencies)
        self.project_panel.status.connect(lambda m: self.statusBar().showMessage(m, 5000))

        self.center = QTabWidget()
        self.center.setDocumentMode(True)
        self.preview = PreviewPanel()
        self.center.addTab(self.preview, tr("ws.preview"))
        self.editors = EditorTabs()
        self.editors.status.connect(lambda m: self.statusBar().showMessage(m, 5000))
        self.center.addTab(self.editors, tr("ws.code"))
        diff = QWidget()
        diff.setObjectName("Panel")
        dl = QVBoxLayout(diff)
        dl.setContentsMargins(24, 24, 24, 24)
        dl.addWidget(MilestoneNotice(tr("ws.diff"), "M3", tr("ws.diff_notice")))
        dl.addStretch(1)
        self.center.addTab(diff, tr("ws.diff"))
        review = QWidget()
        review.setObjectName("Panel")
        rl = QVBoxLayout(review)
        rl.setContentsMargins(24, 24, 24, 24)
        rl.addWidget(MilestoneNotice(tr("ws.review"), "M4", tr("ws.review_notice")))
        rl.addStretch(1)
        self.center.addTab(review, tr("ws.review"))

        self.assistant = AssistantPanel(self.connections, self.budget, self.db, lambda: self.settings)
        self.assistant.open_connections.connect(self.show_connections)
        self.assistant.usage_changed.connect(self._refresh_ai_status)
        self.bottom = BottomPanel(self.db)

        h = QSplitter(Qt.Orientation.Horizontal)
        h.addWidget(self.project_panel)
        h.addWidget(self.center)
        h.addWidget(self.assistant)
        h.setStretchFactor(0, 0)
        h.setStretchFactor(1, 1)
        h.setStretchFactor(2, 0)
        h.setSizes([280, 800, 360])
        h.setChildrenCollapsible(False)
        v = QSplitter(Qt.Orientation.Vertical)
        v.addWidget(h)
        v.addWidget(self.bottom)
        v.setStretchFactor(0, 1)
        v.setSizes([620, 200])
        self.splitter_h, self.splitter_v = h, v
        return v

    # ---- navigation -------------------------------------------------------------
    def show_dashboard(self) -> None:
        self.dashboard.refresh()
        self.stack.setCurrentIndex(0)
        self._refresh_project_combo()
        for a in self._editor_actions:
            a.setEnabled(False)

    def _refresh_project_combo(self) -> None:
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem(tr("tb.no_project"), None)
        for rec in self.projects.list_projects():
            self.project_combo.addItem(rec.name, rec.id)
        if self.current:
            idx = self.project_combo.findData(self.current.id)
            self.project_combo.setCurrentIndex(max(0, idx))
        self.project_combo.blockSignals(False)

    def _project_combo_changed(self, idx: int) -> None:
        pid = self.project_combo.itemData(idx)
        if pid is None:
            self.show_dashboard()
        elif not self.current or pid != self.current.id:
            self.open_project(pid)

    def open_project(self, pid: int) -> None:
        rec = self.projects.get(pid)
        if not rec.exists:
            QMessageBox.warning(self, tr("dash.missing_folder"), tr("dash.missing_folder_msg", path=rec.path))
            return
        if self.current and self.current.id != pid:
            if not self.editors.close_all():
                return
        self.projects.mark_opened(pid)
        self.current = self.projects.get(pid)
        root = Path(rec.path)
        self.project_panel.set_project(root)
        self.assistant.set_project(root, pid)
        self._refresh_ai_status()
        self.preview.set_project(root)
        self.bottom.refresh_tasks(pid)
        spec = ProjectService.load_spec(root)
        if spec:
            self.platform_combo.setCurrentIndex(self.platform_combo.findData(
                "both" if len(spec.platforms) == 2 else spec.platforms[0]))
        self.stack.setCurrentIndex(1)
        self._refresh_project_combo()
        for a in self._editor_actions:
            a.setEnabled(True)
        self.status_path.setText(f"  {rec.path}")
        self._update_trust_badge()
        self.setWindowTitle(f"{rec.name} — {APP_NAME}")
        readme = root / "app" / "index.tsx"
        if readme.is_file() and self.editors.count() == 0:
            self.editors.open_file(readme)

    def _update_trust_badge(self) -> None:
        if not self.current:
            self.status_trust.setVisible(False)
            return
        self.status_trust.setVisible(True)
        if self.current.trusted:
            set_badge_kind(self.status_trust, tr("status.trusted"), "ok")
        else:
            set_badge_kind(self.status_trust, tr("status.untrusted"), "warn")

    def new_project(self) -> None:
        wiz = ProjectWizard(self.projects, self.settings.workspace_dir, self)
        if wiz.exec() and wiz.created_id:
            self.dashboard.refresh()
            self.open_project(wiz.created_id)
            self.statusBar().showMessage(tr("status.created"), 8000)

    def dashboard_import(self) -> None:
        self.dashboard._import()

    # ---- editor -----------------------------------------------------------------
    def _open_file(self, path: Path) -> None:
        self.editors.open_file(path)
        self.center.setCurrentWidget(self.editors)

    def _save(self) -> None:
        self.editors.save_current()

    def _editor_call(self, name: str) -> None:
        ed = self.editors.current_editor()
        if ed:
            getattr(ed, name)()

    # ---- processes --------------------------------------------------------------
    def _ensure_trusted(self) -> bool:
        if not self.current:
            return False
        if self.current.trusted:
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("trust.title"))
        box.setText(tr("trust.text", name=self.current.name))
        box.setInformativeText(TRUST_WARNING_EN if language() == "en" else TRUST_WARNING_VI)
        trust = box.addButton(tr("trust.accept"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        box.exec()
        if box.clickedButton() is not trust:
            return False
        self.projects.set_trusted(self.current.id, True)
        self.current = self.projects.get(self.current.id)
        self._update_trust_badge()
        return True

    def install_dependencies(self) -> None:
        if not self.current or not self._ensure_trusted():
            return
        root = Path(self.current.path)
        if not (root / "package.json").is_file():
            QMessageBox.warning(self, tr("panel.install"), tr("panel.no_package"))
            return
        self.bottom.setCurrentIndex(0)
        self.runner.start(["npm", "install", "--no-audit", "--no-fund"], root, "npm-install", self.current.id,
                          node_path=self.settings.tool_paths.get("node"))

    def _runner_state(self, running: bool) -> None:
        self.a_stop.setEnabled(running)
        self.bottom.btn_stop.setEnabled(running)
        self.project_panel.btn_install.setEnabled(not running)
        if self.current:
            self.bottom.refresh_tasks(self.current.id)

    def _runner_finished(self, job_id: str, code: int) -> None:
        self._runner_state(False)
        if self.current:
            self.project_panel.refresh()
            self.preview.set_project(Path(self.current.path))

    # ---- AI (M2) -----------------------------------------------------------------
    def _refresh_ai_status(self) -> None:
        n = len(self.connections.connected())
        set_badge_kind(self.ai_badge, tr("tb.ai_status", n=n) if n else tr("assist.no_provider"), "ok" if n else "warn")
        limit = self.budget.session_limit()
        spent = self.budget.spent_session()
        text = tr("tb.budget", spent=usd(spent), limit=usd(limit) if limit else tr("usage.no_limit"))
        kind = "err" if limit and spent >= limit else "warn" if limit and spent >= 0.8 * limit else "ok"
        set_badge_kind(self.budget_badge, text, kind)

    def show_connections(self) -> None:
        dlg = ConnectionsDialog(self.connections, self)
        dlg.changed.connect(self._on_ai_changed)
        dlg.exec()
        self._on_ai_changed()

    def _on_ai_changed(self, _provider_id: str | None = None) -> None:
        self.assistant.reload_providers()
        self._refresh_ai_status()

    def show_usage(self) -> None:
        UsageDialog(self.budget, self.current.id if self.current else None, self.assistant.project_limit(), self).exec()
        self._refresh_ai_status()

    # ---- dialogs ----------------------------------------------------------------
    def show_doctor(self) -> None:
        DoctorDialog(self.settings.tool_paths, self.settings.workspace_dir, self).exec()

    def show_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self.db, self)
        if dlg.exec():
            lang_changed = dlg.settings.language != self.settings.language
            self.settings = dlg.settings
            save_settings(self.settings)
            self.assistant._load_history_list()
            apply_theme(QApplication.instance(), self.settings.theme)
            if lang_changed:
                QMessageBox.information(self, tr("settings.title"), tr("settings.restart"))

    def _toggle_theme(self) -> None:
        self.settings.theme = "light" if self.settings.theme == "dark" else "dark"
        apply_theme(QApplication.instance(), self.settings.theme)
        save_settings(self.settings)
        for ed in self.editors.editors():
            ed.highlighter.setDocument(None)
            ed.highlighter = CodeHighlighter(ed.document(), lang_for(ed.path))
            ed.line_area.update()

    def closeEvent(self, e) -> None:  # noqa: N802
        if self.runner.running:
            if QMessageBox.question(self, APP_NAME, tr("close.running")) != QMessageBox.StandardButton.Yes:
                e.ignore()
                return
            self.runner.stop()
        if not self.editors.close_all():
            e.ignore()
            return
        if self.assistant.stream:
            self.assistant.stop()
            self.assistant.stream.wait(5000)
        self.settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode()
        save_settings(self.settings)
        e.accept()
