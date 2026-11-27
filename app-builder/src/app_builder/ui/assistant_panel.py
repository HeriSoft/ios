"""AI ASSISTANT panel.

M2: chat streaming với provider đã kết nối (chọn provider/model, Dừng, chi phí từng lượt, ngân sách).
Lập kế hoạch / tạo / sửa file / áp dụng diff là M3 — các nút đó vẫn vô hiệu hóa và gắn nhãn milestone.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)

from app_builder.agent.budget import BudgetManager, estimate_tokens
from app_builder.core.config import AppSettings
from app_builder.core.database import Database
from app_builder.core.i18n import tr
from app_builder.core.schemas import ProjectSpec, utcnow_iso
from app_builder.providers.base import PROVIDERS, AIRequest, ChatMessage, Done, ProviderError, Usage
from app_builder.services.ai_connections import ConnectionManager
from app_builder.services.project_service import ProjectService
from app_builder.ui.ai_worker import ChatStream
from app_builder.ui.connections_dialog import error_text
from app_builder.ui.usage_dialog import usd
from app_builder.ui.widgets import MilestoneNotice, badge, label, set_badge_kind

# Nút của milestone sau (vẫn khóa)
ACTIONS = [("assist.plan", "M3"), ("assist.create", "M3"), ("assist.edit", "M3"), ("assist.review", "M4"),
           ("assist.fix", "M3"), ("assist.apply", "M3"), ("assist.reject", "M3"), ("assist.undo", "M3")]

# Chế độ trong spec → số token đầu ra tối đa mỗi lượt (cũng là mức giữ chỗ ngân sách)
MAX_OUTPUT_BY_MODE = {"economy": 4_000, "balanced": 16_000, "advanced": 64_000}

SYSTEM_PROMPT = (
    "Bạn là trợ lý lập trình trong App Builder AI, giúp người dùng xây app mobile React Native + Expo + "
    "TypeScript + Expo Router. Trả lời bằng ngôn ngữ người dùng dùng (mặc định tiếng Việt), ngắn gọn, có ví dụ "
    "code khi hữu ích. Ở phiên bản này bạn chỉ tư vấn: không tự sửa file; nếu cần thay đổi code, hãy trình bày "
    "đoạn code để người dùng tự áp dụng."
)


def build_system_prompt(spec: ProjectSpec | None) -> str:
    if not spec:
        return SYSTEM_PROMPT
    lines = [SYSTEM_PROMPT, "", "Thông tin dự án hiện tại:",
             f"- Tên: {spec.name}", f"- Mô tả: {spec.description or '—'}",
             f"- Mẫu: {spec.template} (Expo SDK {spec.expo_sdk}); nền tảng: {', '.join(spec.platforms)}",
             f"- Lĩnh vực: {', '.join(spec.categories) or '—'}"]
    if spec.main_prompt:
        lines.append(f"- Yêu cầu chính: {spec.main_prompt}")
    if spec.features:
        lines.append("- Chức năng: " + "; ".join(spec.features))
    if spec.screens:
        lines.append("- Màn hình: " + "; ".join(f"{s.route} ({s.title})" for s in spec.screens))
    return "\n".join(lines)


class AssistantPanel(QWidget):
    open_connections = Signal()
    usage_changed = Signal()

    def __init__(self, connections: ConnectionManager | None = None, budget: BudgetManager | None = None,
                 db: Database | None = None, settings: Callable[[], AppSettings] | None = None) -> None:
        super().__init__()
        self.cm, self.budget, self.db = connections, budget, db
        self._settings = settings or AppSettings
        self.project_id: int | None = None
        self.spec: ProjectSpec | None = None
        self.history: list[ChatMessage] = []
        self.conversation_id: int | None = None
        self.stream: ChatStream | None = None
        self._reply = ""
        self._approved_unknown: set[tuple[str, str]] = set()
        self.setObjectName("Panel")

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
        prow = QHBoxLayout()
        self.provider = QComboBox()
        self.provider.currentIndexChanged.connect(self._provider_changed)
        prow.addWidget(self.provider, 2)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.setToolTip(tr("assist.model_tip"))
        prow.addWidget(self.model, 3)
        self.btn_conn = QToolButton()
        self.btn_conn.setText("⚙")
        self.btn_conn.setToolTip(tr("conn.title"))
        self.btn_conn.clicked.connect(self.open_connections)
        prow.addWidget(self.btn_conn)
        cl.addLayout(prow)
        self.status = badge("")
        cl.addWidget(self.status)
        cl.addWidget(MilestoneNotice(tr("assist.notice_title"), "M3", tr("assist.notice_m2")))

        split = QSplitter(Qt.Orientation.Vertical)
        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText(tr("assist.transcript_ph"))
        split.addWidget(self.transcript)
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(tr("assist.prompt_ph"))
        split.addWidget(self.prompt)
        split.setSizes([300, 110])
        cl.addWidget(split, 1)
        QShortcut(QKeySequence("Ctrl+Return"), self.prompt, activated=self.send)

        srow = QHBoxLayout()
        self.btn_send = QPushButton(tr("assist.send"))
        self.btn_send.setObjectName("Primary")
        self.btn_send.clicked.connect(self.send)
        self.btn_stop = QPushButton(tr("assist.stop"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_new = QPushButton(tr("assist.new_chat"))
        self.btn_new.clicked.connect(self.new_chat)
        srow.addWidget(self.btn_send)
        srow.addWidget(self.btn_stop)
        srow.addWidget(self.btn_new)
        cl.addLayout(srow)
        self.usage_label = label("", wrap=True)
        cl.addWidget(self.usage_label)

        grid = QGridLayout()
        for i, (key, ms) in enumerate(ACTIONS):
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
        self.hist_note = label(tr("assist.history_notice"), wrap=True)
        hl.addWidget(self.hist_note)
        self.hist_list = QListWidget()
        self.hist_list.currentItemChanged.connect(self._show_conversation)
        hl.addWidget(self.hist_list, 1)
        self.hist_view = QPlainTextEdit()
        self.hist_view.setReadOnly(True)
        hl.addWidget(self.hist_view, 2)
        self.tabs.addTab(hist, tr("assist.history"))

        self.reload_providers()

    # ---- provider / model ------------------------------------------------------------
    def reload_providers(self) -> None:
        current = self.provider.currentData()
        self.provider.blockSignals(True)
        self.provider.clear()
        connected = self.cm.connected() if self.cm else []
        for pid in connected:
            self.provider.addItem(PROVIDERS[pid].name, pid)
        if not connected:
            self.provider.addItem(tr("assist.no_provider"), None)
        preferred = current or (self.spec.ai.provider if self.spec else None)
        idx = self.provider.findData(preferred) if preferred else -1
        self.provider.setCurrentIndex(max(idx, 0))
        self.provider.blockSignals(False)
        self._provider_changed()

    def _provider_changed(self) -> None:
        pid = self.provider.currentData()
        keep = self.model.currentText().strip()
        self.model.clear()
        if not pid or not self.cm:
            set_badge_kind(self.status, tr("assist.not_connected"), "warn")
            self._set_enabled(False)
            return
        models, _ = self.cm.cached_models(pid)
        for m in models:
            self.model.addItem(m.label, m.id)
        wanted = keep or (self.spec.ai.model if self.spec and self.spec.ai.provider == pid else "")
        if not wanted and pid == "anthropic":
            wanted = "claude-opus-5-5"
        if wanted:
            idx = self.model.findData(wanted)
            if idx >= 0:
                self.model.setCurrentIndex(idx)
            else:
                self.model.setEditText(wanted)
        set_badge_kind(self.status, tr("assist.ready", name=PROVIDERS[pid].name) if models
                       else tr("assist.no_models"), "ok" if models else "warn")
        self._set_enabled(True)

    def _set_enabled(self, on: bool) -> None:
        busy = self.stream is not None
        self.prompt.setEnabled(on)
        self.btn_send.setEnabled(on and not busy)
        self.model.setEnabled(on and not busy)
        self.provider.setEnabled(not busy)

    def current_model(self) -> str:
        data = self.model.currentData()
        text = self.model.currentText().strip()
        # Nếu người dùng gõ tay model id thì ưu tiên văn bản
        if data and self.model.itemText(self.model.currentIndex()) == text:
            return data
        return text

    # ---- project -----------------------------------------------------------------------
    def set_project(self, root: Path | None, project_id: int | None = None) -> None:
        if self.stream:
            self.stop()
        self.project_id = project_id
        self.spec = ProjectService.load_spec(root) if root else None
        self.new_chat()
        self.reload_providers()
        self._load_history_list()
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

    def project_limit(self) -> float | None:
        return self.spec.ai.budget_usd_project if self.spec else None

    # ---- chat ----------------------------------------------------------------------------
    def new_chat(self) -> None:
        if self.stream:
            return
        self.history = []
        self.conversation_id = None
        self.transcript.clear()
        self.usage_label.setText("")

    def _append(self, text: str) -> None:
        cur = self.transcript.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(text)
        self.transcript.setTextCursor(cur)
        self.transcript.ensureCursorVisible()

    def send(self) -> None:
        if self.stream or not self.cm or not self.budget:
            return
        text = self.prompt.toPlainText().strip()
        pid = self.provider.currentData()
        model = self.current_model()
        if not text:
            return
        if not pid or not model:
            self.usage_label.setText("✖ " + tr("assist.choose_model"))
            return
        try:
            provider = self.cm.provider(pid)
        except Exception as exc:
            self.usage_label.setText("✖ " + error_text(exc))
            return
        mode = self.spec.ai.mode if self.spec else "balanced"
        max_out = MAX_OUTPUT_BY_MODE.get(mode, 16_000)
        system = build_system_prompt(self.spec)
        messages = [*self.history, ChatMessage("user", text)]
        prompt_text = system + "\n".join(m.content for m in messages)

        decision = self.budget.check(pid, model, prompt_text, max_out, self.project_id, self.project_limit())
        if not decision.allowed:
            scope = decision.reason.removeprefix("over_")
            QMessageBox.warning(self, tr("budget.title"), tr(f"budget.over_{scope}", estimate=usd(decision.estimate_usd)))
            return
        if decision.needs_confirmation and (pid, model) not in self._approved_unknown:
            if QMessageBox.question(self, tr("budget.title"), tr("budget.unknown_price", model=model)) \
                    != QMessageBox.StandardButton.Yes:
                return
            self._approved_unknown.add((pid, model))
        warn = " · ".join(tr(f"budget.warn_{w}") for w in decision.warn)

        request = AIRequest(model=model, messages=messages, system=system, max_output_tokens=max_out)
        self.budget.reserve(request.request_id, decision.estimate_usd, self.project_id)
        self.prompt.clear()
        self.history.append(ChatMessage("user", text))
        self._save_message("user", text)
        self._append(("\n\n" if self.transcript.toPlainText() else "") + f"🧑 {text}\n\n🤖 {model}:\n")
        self._reply = ""
        self.usage_label.setText((("⚠ " + warn + "\n") if warn else "") + tr("assist.streaming"))

        s = ChatStream(provider, request, self)
        s.text.connect(self._on_text)
        s.done.connect(lambda d, s=s: self._on_done(s, d))
        s.failed.connect(lambda e, s=s: self._on_failed(s, e))
        s.ended.connect(self._on_ended)
        self.stream = s
        self._pending = (pid, request, warn)
        self.btn_stop.setEnabled(True)
        self._set_enabled(True)
        s.start()

    def stop(self) -> None:
        if self.stream:
            self.stream.cancel()

    def _on_text(self, chunk: str) -> None:
        self._reply += chunk
        self._append(chunk)

    def _finish_record(self, request: AIRequest, pid: str, usage: Usage, status: str, model: str,
                       approximate: bool) -> float | None:
        cost = self.budget.record(request.request_id, pid, model, usage, status, self.project_id, approximate)
        self.usage_changed.emit()
        return cost

    def _on_done(self, s: ChatStream, done: Done) -> None:
        pid, request, warn = self._pending
        usage = done.usage
        approximate = done.fallback_used
        if done.stop_reason == "cancelled" and not usage.output_tokens and self._reply:
            usage = Usage(usage.input_tokens or estimate_tokens(request.system + "".join(m.content for m in request.messages)),
                          estimate_tokens(self._reply), usage.cached_tokens)
            approximate = True
        model = done.model if done.model and self.budget.prices.lookup(pid, done.model) else request.model
        status = "cancelled" if done.stop_reason == "cancelled" else "ok"
        cost = self._finish_record(request, pid, usage, status, model, approximate or model != (done.model or model))
        if self._reply:
            self.history.append(ChatMessage("assistant", self._reply))
            self._save_message("assistant", self._reply)
        note = ""
        if done.stop_reason == "cancelled":
            note = " · " + tr("assist.cancelled")
        elif done.stop_reason in ("max_tokens", "length", "MAX_TOKENS", "max_output_tokens"):
            note = " · " + tr("assist.truncated")
        elif done.stop_reason == "refusal":
            note = " · " + tr("assist.refused")
        if done.fallback_used:
            note += " · " + tr("assist.fallback", model=done.model or "?")
        self.usage_label.setText((("⚠ " + warn + "\n") if warn else "") + tr(
            "assist.usage_line", inp=usage.input_tokens, cached=usage.cached_tokens, out=usage.output_tokens,
            cost=usd(cost, approx=approximate)) + note)

    def _on_failed(self, s: ChatStream, err: ProviderError) -> None:
        pid, request, _ = self._pending
        self.budget.record(request.request_id, pid, request.model, Usage(), "error", self.project_id)
        self.usage_changed.emit()
        if self._reply:
            self.history.append(ChatMessage("assistant", self._reply))
        else:
            # Lượt lỗi không có trả lời: bỏ câu hỏi khỏi ngữ cảnh để lần gửi lại không bị lặp
            if self.history and self.history[-1].role == "user":
                self.history.pop()
        self._append("\n✖ " + error_text(err) + "\n")
        self.usage_label.setText("✖ " + tr(f"ai.err.{err.kind.value}") +
                                 (" · " + tr("ai.retryable") if err.kind.retryable else ""))

    def _on_ended(self) -> None:
        self.stream = None
        self.btn_stop.setEnabled(False)
        self._set_enabled(bool(self.provider.currentData()))

    # ---- lịch sử (chỉ khi bật trong Cài đặt) -------------------------------------------------
    def _keep_history(self) -> bool:
        try:
            return bool(self._settings().keep_message_history)
        except Exception:
            return False

    def _save_message(self, role: str, content: str) -> None:
        if not self.db or not self._keep_history():
            return
        if self.conversation_id is None:
            title = content.splitlines()[0][:60] if role == "user" else tr("assist.history")
            self.conversation_id = self.db.execute(
                "INSERT INTO conversations(project_id, title, created_at) VALUES (?,?,?)",
                (self.project_id, title, utcnow_iso()))
        self.db.execute("INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?,?,?,?)",
                        (self.conversation_id, role, content, utcnow_iso()))
        self._load_history_list()

    def _load_history_list(self) -> None:
        self.hist_list.clear()
        self.hist_view.clear()
        if not self.db:
            return
        self.hist_note.setText(tr("assist.history_notice") + ("" if self._keep_history() else "\n" + tr("assist.history_off")))
        rows = self.db.query("SELECT id, title, created_at FROM conversations WHERE project_id IS ? ORDER BY id DESC",
                             (self.project_id,))
        for r in rows:
            it = QListWidgetItem(f"{r['created_at'][:16].replace('T', ' ')} · {r['title']}")
            it.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.hist_list.addItem(it)

    def _show_conversation(self, item: QListWidgetItem | None, _prev=None) -> None:
        if not item or not self.db:
            return
        rows = self.db.query("SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id",
                             (item.data(Qt.ItemDataRole.UserRole),))
        self.hist_view.setPlainText("\n\n".join(("🧑 " if r["role"] == "user" else "🤖 ") + r["content"] for r in rows))
