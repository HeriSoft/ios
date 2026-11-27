"""AI ASSISTANT panel. M1: hiển thị spec/yêu cầu thật của project; chat/generate cần provider (M2) + agent (M3).
Các nút chưa hoạt động được vô hiệu hóa và gắn nhãn milestone, không giả lập phản hồi AI."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from app_builder.core.i18n import tr
from app_builder.services.project_service import ProjectService
from app_builder.ui.widgets import MilestoneNotice, badge, label

ACTIONS = [("assist.plan", "M3"), ("assist.create", "M3"), ("assist.edit", "M3"), ("assist.review", "M4"),
           ("assist.fix", "M3"), ("assist.stop", "M2"), ("assist.apply", "M3"), ("assist.reject", "M3"),
           ("assist.undo", "M3")]


class AssistantPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
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
        self.provider.addItem(tr("assist.no_provider"))
        self.provider.setEnabled(False)
        prow.addWidget(self.provider, 1)
        prow.addWidget(badge(tr("assist.not_connected"), "warn"))
        cl.addLayout(prow)
        cl.addWidget(MilestoneNotice(tr("assist.notice_title"), "M2", tr("assist.notice")))
        self.scope = QComboBox()
        for key in ("assist.scope_app", "assist.scope_screen", "assist.scope_file", "assist.scope_component"):
            self.scope.addItem(tr(key))
        self.scope.setEnabled(False)
        cl.addWidget(self.scope)
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(tr("assist.prompt_ph"))
        self.prompt.setEnabled(False)
        cl.addWidget(self.prompt, 1)
        grid = QGridLayout()
        for i, (key, ms) in enumerate(ACTIONS):
            b = QPushButton(tr(key))
            b.setEnabled(False)
            b.setToolTip(tr("common.planned", milestone=ms))
            grid.addWidget(b, i // 3, i % 3)
        cl.addLayout(grid)
        self.tabs.addTab(chat, tr("assist.chat"))

        self.plan = QPlainTextEdit()
        self.plan.setReadOnly(True)
        self.tabs.addTab(self.plan, tr("assist.spec"))

        hist = QWidget()
        hl = QVBoxLayout(hist)
        hl.setContentsMargins(10, 10, 10, 10)
        hl.addWidget(MilestoneNotice(tr("assist.history"), "M2–M3", tr("assist.history_notice")))
        hl.addStretch(1)
        self.tabs.addTab(hist, tr("assist.history"))

    def set_project(self, root: Path | None) -> None:
        spec = ProjectService.load_spec(root) if root else None
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
