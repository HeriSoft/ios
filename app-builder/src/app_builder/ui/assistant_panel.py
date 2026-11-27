"""AI ASSISTANT panel (M2): chọn provider/model đã kết nối, chat streaming, Dừng, đính kèm ảnh/file đang mở
(có cảnh báo dữ liệu gửi ra ngoài), kiểm tra ngân sách trước mỗi request, hiển thị usage/chi phí.

Lập kế hoạch / sinh patch / Áp dụng / Hoàn tác thuộc M3 — các nút đó vẫn bị vô hiệu hóa và gắn nhãn."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QMessageBox, QPlainTextEdit, QPushButton,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from app_builder.agent.budget import BudgetLimits, BudgetManager
from app_builder.agent.chat_service import ChatSession, ChatTurnResult
from app_builder.agent.prompts import build_system
from app_builder.core.database import Database
from app_builder.core.i18n import tr
from app_builder.core.schemas import ProjectSpec, utcnow_iso
from app_builder.providers.base import AIEvent, ContextFile, ImageInput
from app_builder.providers.registry import SPECS, ProviderRegistry
from app_builder.services.project_service import ProjectService
from app_builder.ui.async_runner import AsyncStream
from app_builder.ui.widgets import MilestoneNotice, label

M3_ACTIONS = [("assist.plan", "M3"), ("assist.create", "M3"), ("assist.edit", "M3"), ("assist.review", "M4"),
              ("assist.fix", "M3"), ("assist.apply", "M3"), ("assist.reject", "M3"), ("assist.undo", "M3")]
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_CONTEXT_FILE_CHARS = 60_000


class AssistantPanel(QWidget):
    usage_changed = Signal()
    open_connections = Signal()
    selection_changed = Signal()

    def __init__(self, registry: ProviderRegistry | None = None, budget: BudgetManager | None = None,
                 db: Database | None = None, keep_history: Callable[[], bool] | None = None) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.reg = registry
        self.budget = budget
        self.db = db
        self.keep_history = keep_history or (lambda: False)
        self.current_file: Callable[[], tuple[Path, str] | None] = lambda: None
        self.root: Path | None = None
        self.project_id: int | None = None
        self.spec: ProjectSpec | None = None
        self.session: ChatSession | None = None
        self.stream: AsyncStream | None = None
        self.images: list[tuple[str, ImageInput]] = []
        self._consented: set[str] = set()
        self._conversation_id: int | None = None
        self._last: ChatTurnResult | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(label(tr("assist.title").upper(), "SectionTitle"))
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        lay.addWidget(self.tabs, 1)

        chat = QWidget()
        cl = QVBoxLayout(chat)
        cl.setContentsMargins(10, 8, 10, 10)
        cl.setSpacing(6)
        prow = QHBoxLayout()
        self.provider = QComboBox()
        self.provider.currentIndexChanged.connect(self._provider_changed)
        self.model = QComboBox()
        self.model.setMinimumWidth(140)
        self.model.activated.connect(self._model_changed)
        self.btn_conn = QPushButton("🔌")
        self.btn_conn.setToolTip(tr("assist.connections"))
        self.btn_conn.setFixedWidth(36)
        self.btn_conn.clicked.connect(self.open_connections.emit)
        prow.addWidget(self.provider, 1)
        prow.addWidget(self.model, 1)
        prow.addWidget(self.btn_conn)
        cl.addLayout(prow)
        self.notice = MilestoneNotice(tr("assist.connect_title"), "", tr("assist.connect_hint"))
        cl.addWidget(self.notice)

        self.transcript = QTextBrowser()
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setPlaceholderText(tr("assist.empty_chat"))
        cl.addWidget(self.transcript, 3)

        srow = QHBoxLayout()
        self.scope = QComboBox()
        self.scope.addItem(tr("assist.scope_none"), "none")
        self.scope.addItem(tr("assist.scope_file"), "file")
        self.scope.addItem(tr("assist.scope_screen") + " — M3", "screen")
        self.scope.model().item(2).setEnabled(False)
        srow.addWidget(self.scope, 1)
        self.btn_img = QPushButton("🖼")
        self.btn_img.setToolTip(tr("assist.attach_image"))
        self.btn_img.setFixedWidth(36)
        self.btn_img.clicked.connect(self._attach_image)
        srow.addWidget(self.btn_img)
        cl.addLayout(srow)
        self.attach_label = label("", "Muted", wrap=True)
        cl.addWidget(self.attach_label)

        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(tr("assist.prompt_ph2"))
        self.prompt.setMaximumHeight(110)
        cl.addWidget(self.prompt)
        QShortcut(QKeySequence("Ctrl+Return"), self.prompt, activated=self.send)
        QShortcut(QKeySequence("Ctrl+Enter"), self.prompt, activated=self.send)
        brow = QHBoxLayout()
        self.btn_new = QPushButton(tr("assist.new_chat"))
        self.btn_new.clicked.connect(self.new_chat)
        self.btn_stop = QPushButton("■ " + tr("assist.stop"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_send = QPushButton(tr("assist.send"))
        self.btn_send.setObjectName("Primary")
        self.btn_send.clicked.connect(self.send)
        brow.addWidget(self.btn_new)
        brow.addStretch(1)
        brow.addWidget(self.btn_stop)
        brow.addWidget(self.btn_send)
        cl.addLayout(brow)
        self.status = label("", "Muted", wrap=True)
        cl.addWidget(self.status)
        grid = QGridLayout()
        for i, (key, ms) in enumerate(M3_ACTIONS):
            b = QPushButton(tr(key))
            b.setEnabled(False)
            b.setToolTip(tr("common.planned", milestone=ms))
            grid.addWidget(b, i // 4, i % 4)
        cl.addLayout(grid)
        self.tabs.addTab(chat, tr("assist.chat"))

        self.plan = QPlainTextEdit()
        self.plan.setReadOnly(True)
        self.tabs.addTab(self.plan, tr("assist.spec"))

        hist = QWidget()
        hl = QVBoxLayout(hist)
        hl.setContentsMargins(10, 10, 10, 10)
        self.history_view = QTextBrowser()
        hl.addWidget(label(tr("assist.history_note"), "Muted", wrap=True))
        hl.addWidget(self.history_view, 1)
        self.tabs.addTab(hist, tr("assist.history"))
        self.refresh_providers()

    # ---- provider/model ----------------------------------------------------------
    def refresh_providers(self) -> None:
        connected = self.reg.connected_providers() if self.reg else []
        cur = self.provider.currentData()
        self.provider.blockSignals(True)
        self.provider.clear()
        for pid in connected:
            self.provider.addItem(SPECS[pid].name, pid)
        if not connected:
            self.provider.addItem(tr("assist.no_provider"), None)
        idx = self.provider.findData(cur) if cur else -1
        if idx < 0 and self.spec and self.spec.ai.provider:
            idx = self.provider.findData(self.spec.ai.provider)
        self.provider.setCurrentIndex(max(0, idx))
        self.provider.blockSignals(False)
        self.notice.setVisible(not connected)
        self._provider_changed()

    def _provider_changed(self, *_):
        pid = self.provider.currentData()
        self.model.clear()
        busy = self.stream is not None
        for w in (self.model, self.prompt, self.btn_send, self.scope):
            w.setEnabled(bool(pid) and not busy)
        if pid and self.reg:
            models, _ = self.reg.cached_models(pid)
            for m in models:
                self.model.addItem(m.label(), m.id)
            cfg = self.reg.get_config(pid)
            want = cfg.selected_model or SPECS[pid].default_model or ""
            idx = self.model.findData(want)
            if idx >= 0:
                self.model.setCurrentIndex(idx)
        self.btn_img.setEnabled(bool(pid) and not busy and self._vision_allowed())
        self.selection_changed.emit()

    def _model_changed(self, *_):
        pid, mid = self.provider.currentData(), self.model.currentData()
        if pid and mid and self.reg:
            self.reg.select_model(pid, mid)
        self.btn_img.setEnabled(bool(pid) and self._vision_allowed())
        self.selection_changed.emit()

    def _vision_allowed(self) -> bool:
        pid, mid = self.provider.currentData(), self.model.currentData()
        if not pid or not mid or not self.reg or pid == "deepseek":
            return False
        models, _ = self.reg.cached_models(pid)
        m = next((x for x in models if x.id == mid), None)
        return m is None or m.capabilities.get("vision") is not False

    def selection_label(self) -> str:
        pid, mid = self.provider.currentData(), self.model.currentData()
        return f"{SPECS[pid].name} · {mid}" if pid and mid else tr("assist.no_provider")

    # ---- project ----------------------------------------------------------------
    def set_project(self, root: Path | None, project_id: int | None = None) -> None:
        self.root = root
        self.project_id = project_id
        self.spec = ProjectService.load_spec(root) if root else None
        self._render_spec()
        self.new_chat()
        self.refresh_providers()
        self._load_history()

    def _render_spec(self) -> None:
        spec = self.spec
        if not spec:
            self.plan.setPlainText(tr("panel.no_spec"))
            return
        lines = [
            f"# {spec.name}", spec.description, "",
            f"{tr('assist.spec_template')}: {spec.template}   Expo SDK {spec.expo_sdk}",
            f"{tr('assist.spec_categories')}: {', '.join(spec.categories)}",
            f"{tr('assist.spec_platforms')}: {', '.join(spec.platforms)}",
            f"Android: {spec.android_package}   iOS: {spec.ios_bundle_id}",
            f"{tr('assist.spec_ai')}: {spec.ai.provider or '—'} / {spec.ai.model or '—'} · {spec.ai.mode}"
            f" · ${spec.ai.budget_usd_project or 0:g}/project",
            "", f"## {tr('assist.spec_prompt')}", spec.main_prompt or "—",
            "", f"## {tr('assist.spec_features')}", *([f"- {f}" for f in spec.features] or ["—"]),
            "", f"## {tr('assist.spec_screens')}", *[f"- {s.route} — {s.title}" for s in spec.screens],
            "", f"## {tr('assist.spec_tests')}", *[f"- [ ] {t}" for t in spec.acceptance_tests],
        ]
        if spec.references:
            lines += ["", f"## {tr('assist.spec_refs')}", *[f"- {r}" for r in spec.references]]
        self.plan.setPlainText("\n".join(lines))

    def overrides(self) -> BudgetLimits | None:
        if not self.spec:
            return None
        return BudgetLimits(project_usd=self.spec.ai.budget_usd_project, session_usd=self.spec.ai.budget_usd_session)

    # ---- attachments ----------------------------------------------------------------
    def _attach_image(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, tr("assist.attach_image"), "", "Images (*.png *.jpg *.jpeg)")
        for f in files:
            p = Path(f)
            if p.stat().st_size > MAX_IMAGE_BYTES:
                QMessageBox.warning(self, tr("assist.title"), tr("wiz.refs_too_big", name=p.name))
                continue
            mt = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            self.images.append((p.name, ImageInput(mt, p.read_bytes())))
        self._update_attach_label()

    def _update_attach_label(self) -> None:
        names = [n for n, _ in self.images]
        self.attach_label.setText(tr("assist.attached", names=", ".join(names)) if names else "")

    # ---- chat ---------------------------------------------------------------------
    def new_chat(self) -> None:
        if self.stream is not None:
            return
        self.session = None
        self._conversation_id = None
        self.transcript.clear()
        self.status.setText("")
        self.images.clear()
        self._update_attach_label()

    def _append_html(self, html_text: str) -> None:
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.transcript.insertHtml(html_text)
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)

    def _append_text(self, text: str) -> None:
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.transcript.insertPlainText(text)
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)

    def _context_files(self) -> list[ContextFile]:
        if self.scope.currentData() != "file":
            return []
        cur = self.current_file()
        if not cur:
            return []
        path, content = cur
        rel = str(path)
        if self.root:
            try:
                rel = path.relative_to(self.root).as_posix()
            except ValueError:
                pass
        if self.spec and rel in self.spec.locked_files:
            rel += " (KHÓA — không đề xuất sửa)"
        return [ContextFile(rel, content[:MAX_CONTEXT_FILE_CHARS])]

    def _confirm(self, title: str, text: str) -> bool:
        return QMessageBox.question(self, title, text) == QMessageBox.StandardButton.Yes

    def _consent(self, pid: str, what: list[str]) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(tr("assist.consent_title"))
        box.setText(tr("assist.consent_text", provider=SPECS[pid].name))
        box.setInformativeText("• " + "\n• ".join(what))
        cb = QCheckBox(tr("assist.consent_remember"))
        box.setCheckBox(cb)
        box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if box.exec() != QMessageBox.StandardButton.Ok:
            return False
        if cb.isChecked():
            self._consented.add(pid)
        return True

    def send(self) -> None:
        if self.stream is not None or not self.reg or not self.budget:
            return
        text = self.prompt.toPlainText().strip()
        pid, mid = self.provider.currentData(), self.model.currentData()
        if not text:
            return
        if not pid or not mid:
            QMessageBox.information(self, tr("assist.title"), tr("assist.pick_model"))
            return
        ctx = self._context_files()
        if self.scope.currentData() == "file" and not ctx:
            QMessageBox.information(self, tr("assist.title"), tr("assist.no_open_file"))
            return
        if self.session is None or self.session.provider_id != pid or self.session.model != mid:
            self.session = ChatSession(pid, mid, self.spec.ai.mode if self.spec else "economy")
        req = self.session.build_request(text, build_system(self.spec), ctx)
        req.messages[-1].images = [img for _, img in self.images]

        # 1) Đồng ý gửi dữ liệu ra ngoài (mỗi provider; có thể nhớ trong phiên)
        if not SPECS[pid].test_only and pid not in self._consented:
            what = [tr("assist.send_prompt"), tr("assist.send_spec")]
            what += [tr("assist.send_file", name=f.path) for f in ctx]
            what += [tr("assist.send_image", name=n) for n, _ in self.images]
            if not self._consent(pid, what):
                return

        # 2) Ngân sách
        decision = self.budget.check(pid, req, self.project_id, self.overrides())
        est = f"${decision.estimate_usd:.4f}" if decision.estimate_usd is not None else tr("assist.unknown")
        if decision.status == "blocked":
            QMessageBox.warning(self, tr("assist.budget_title"),
                                "\n".join(decision.messages) + "\n\n" + tr("assist.budget_blocked"))
            return
        if decision.status == "unknown_price" and not self._confirm(
                tr("assist.budget_title"), "\n".join(decision.messages) + "\n\n" + tr("assist.unknown_confirm")):
            return
        if decision.status == "warn" and not self._confirm(
                tr("assist.budget_title"), "\n".join(decision.messages) + "\n\n" + tr("assist.warn_confirm", est=est)):
            return

        # 3) Gửi
        self._append_html(f"<p style='margin-top:10px'><b>🧑 {tr('assist.you')}:</b><br>"
                          f"{html.escape(text).replace(chr(10), '<br>')}</p>")
        if ctx or self.images:
            names = [f.path for f in ctx] + [n for n, _ in self.images]
            self._append_html(f"<p style='color:gray'>📎 {html.escape(', '.join(names))}</p>")
        tag = " [TEST]" if SPECS[pid].test_only else ""
        self._append_html(f"<p><b>🤖 {html.escape(mid)}{tag}:</b><br></p>")
        self.prompt.clear()
        self.images.clear()
        self._update_attach_label()
        self.status.setText(tr("assist.sending", est=est, tokens=decision.input_tokens_est))
        self._persist("user", text)
        provider = self.reg.create(pid)
        session = self.session
        budget = self.budget
        project_id = self.project_id
        self._last = None
        self.stream = AsyncStream(lambda: session.run(provider, req, budget, decision, project_id),
                                  self._on_item, self._on_done, None, self)
        self._set_busy(True)

    def _on_item(self, item) -> None:
        ev, result = item
        self._last = result
        assert isinstance(ev, AIEvent)
        if ev.type == "text_delta":
            self._append_text(ev.text)
        elif ev.type == "warning":
            self._append_html(f"<p style='color:#B7791F'>⚠ {html.escape(ev.text)}</p>")
        elif ev.type == "error" and ev.error:
            self._append_html(f"<p style='color:#D33B62'>✖ {html.escape(ev.error.user_message)}</p>")

    def _on_done(self, how) -> None:
        res = self._last
        self.stream = None
        self._set_busy(False)
        if how == "cancelled":
            self._append_html(f"<p style='color:gray'>■ {tr('assist.cancelled')}</p>")
            self.status.setText(tr("assist.cancelled_note"))
        elif res is not None:
            u = res.usage
            cost = f"${res.cost_usd:.5f}" if res.cost_usd is not None else tr("assist.unknown")
            if u and u.input_tokens is not None:
                self.status.setText(tr("assist.usage", inp=u.input_tokens, cached=u.cached_input_tokens or 0,
                                       out=u.output_tokens or 0, cost=cost))
            elif res.status == "error":
                self.status.setText(tr("assist.error_note"))
            if res.status == "completed":
                self._persist("assistant", res.text)
        self._append_html("<br>")
        self._load_history()
        self.usage_changed.emit()

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.cancel()

    @property
    def busy(self) -> bool:
        return self.stream is not None

    def _set_busy(self, busy: bool) -> None:
        self.btn_stop.setEnabled(busy)
        for w in (self.btn_send, self.provider, self.model, self.btn_new, self.scope, self.prompt):
            w.setEnabled(not busy)
        self.btn_img.setEnabled(not busy and self._vision_allowed())

    # ---- history (opt-in) ------------------------------------------------------------
    def _persist(self, role: str, text: str) -> None:
        if not self.db or not self.keep_history() or not text:
            return
        if self._conversation_id is None:
            self._conversation_id = self.db.execute(
                "INSERT INTO conversations(project_id, title, created_at) VALUES (?,?,?)",
                (self.project_id, text[:60], utcnow_iso()))
        self.db.execute("INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?,?,?,?)",
                        (self._conversation_id, role, text, utcnow_iso()))

    def _load_history(self) -> None:
        if not self.db or self.project_id is None:
            self.history_view.clear()
            return
        rows = self.db.query(
            "SELECT c.title, c.created_at, COUNT(m.id) AS n FROM conversations c LEFT JOIN messages m "
            "ON m.conversation_id=c.id WHERE c.project_id=? GROUP BY c.id ORDER BY c.id DESC LIMIT 50",
            (self.project_id,))
        if not rows:
            self.history_view.setPlainText(tr("assist.history_empty"))
            return
        self.history_view.setPlainText("\n".join(f"{r['created_at'][:16]}  ·  {r['title']}  ({r['n']})" for r in rows))
