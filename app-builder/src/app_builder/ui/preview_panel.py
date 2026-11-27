"""Preview tab. Live preview Expo web thật (process manager + health check + QWebEngineView) thuộc M4.
M1 chỉ hiển thị trạng thái chuẩn bị thật (dependencies đã cài chưa, WebEngine có không) — không hiển thị ảnh giả."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QVBoxLayout, QWidget

from app_builder.core.i18n import tr
from app_builder.services import project_inspect as pi
from app_builder.ui.widgets import MilestoneNotice, label


def webengine_available() -> bool:
    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401
        return True
    except ImportError:
        return False


class PreviewPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Panel")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.addWidget(MilestoneNotice(tr("preview.title"), "M4", tr("preview.notice")))
        self.state = label("", "Muted", wrap=True)
        lay.addWidget(self.state)
        lay.addStretch(1)

    def set_project(self, root: Path | None) -> None:
        if not root:
            self.state.setText("")
            return
        deps = pi.read_dependencies(root)
        lines = [
            ("✔ " if deps["installed"] else "✖ ") + (tr("panel.deps_installed") if deps["installed"] else tr("panel.deps_not_installed")),
            ("✔ " if webengine_available() else "⚠ ") + (tr("preview.webengine_ok") if webengine_available() else tr("preview.webengine_missing")),
            tr("preview.manual", path=str(root)),
        ]
        self.state.setText("\n".join(lines))
