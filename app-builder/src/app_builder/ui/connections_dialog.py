"""Hộp thoại Kết nối AI: key (ẩn/hiện, lưu trong keyring), base URL (chỉ HTTPS), kiểm tra kết nối,
làm mới danh sách model, ngắt kết nối. Mọi lệnh gọi mạng chạy nền, không chặn giao diện."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QToolButton, QVBoxLayout, QWidget,
)

from app_builder.core.i18n import tr
from app_builder.core.redaction import redact
from app_builder.core.secret_store import SecretStore
from app_builder.providers._errors import to_provider_error
from app_builder.providers.base import PROVIDERS, InvalidBaseURL, ProviderError
from app_builder.services.ai_connections import ConnectionManager
from app_builder.ui.widgets import badge, label, run_in_background, set_badge_kind


def error_text(exc: object) -> str:
    if isinstance(exc, ProviderError):
        msg = tr(f"ai.err.{exc.kind.value}")
        return f"{msg}" + (f"\n{redact(exc.detail)[:300]}" if exc.detail else "")
    return redact(str(exc))[:300]


class ProviderCard(QFrame):
    changed = Signal(str)

    def __init__(self, cm: ConnectionManager, provider_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cm, self.pid = cm, provider_id
        self.meta = PROVIDERS[provider_id]
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(self)
        head = QHBoxLayout()
        head.addWidget(label(self.meta.name, "H3"))
        head.addStretch(1)
        self.status = badge("")
        head.addWidget(self.status)
        lay.addLayout(head)

        form = QFormLayout()
        krow = QHBoxLayout()
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setObjectName(f"key_{provider_id}")
        krow.addWidget(self.key, 1)
        self.toggle = QToolButton()
        self.toggle.setText("👁")
        self.toggle.setCheckable(True)
        self.toggle.setToolTip(tr("conn.show_key"))
        self.toggle.toggled.connect(lambda on: self.key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        krow.addWidget(self.toggle)
        form.addRow(tr("conn.api_key"), krow)
        self.base_url = QLineEdit()
        form.addRow(tr("conn.base_url"), self.base_url)
        lay.addLayout(form)
        if self.meta.key_url:
            # Màu link sáng để đọc được trên cả theme tối và sáng
            link = QLabel(f'<a style="color:#5b9dff" href="{self.meta.key_url}">{tr("conn.get_key")}</a>')
            link.setOpenExternalLinks(True)
            lay.addWidget(link)

        btns = QHBoxLayout()
        self.btn_save = QPushButton(tr("common.save"))
        self.btn_test = QPushButton(tr("conn.test"))
        self.btn_models = QPushButton(tr("conn.refresh_models"))
        self.btn_disconnect = QPushButton(tr("conn.disconnect"))
        for b in (self.btn_save, self.btn_test, self.btn_models, self.btn_disconnect):
            btns.addWidget(b)
        btns.addStretch(1)
        lay.addLayout(btns)
        self.result = label("", wrap=True)
        self.result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.result)

        self.btn_save.clicked.connect(self.save)
        self.btn_test.clicked.connect(self.test)
        self.btn_models.clicked.connect(self.refresh_models)
        self.btn_disconnect.clicked.connect(self.disconnect)
        self.reload()

    def reload(self) -> None:
        info = self.cm.info(self.pid)
        self.base_url.setText(info.base_url)
        self.key.clear()
        if self.meta.test_only:
            self.key.setEnabled(False)
            self.base_url.setEnabled(False)
            self.key.setPlaceholderText(tr("conn.fake_no_key"))
        elif info.has_key:
            self.key.setPlaceholderText(tr("conn.key_saved", masked=SecretStore.mask(self.cm.api_key(self.pid))))
        else:
            self.key.setPlaceholderText(tr("conn.key_ph", prefix=self.meta.key_prefix_hint))
        if info.has_key:
            text = tr("conn.connected_n", n=len(info.models)) if info.models else tr("conn.key_set")
            set_badge_kind(self.status, text, "ok")
        else:
            set_badge_kind(self.status, tr("assist.not_connected"), "warn")
        self.btn_disconnect.setEnabled(info.has_key and not self.meta.test_only)
        self.btn_models.setEnabled(info.has_key)

    def _busy(self, on: bool, text: str = "") -> None:
        for b in (self.btn_save, self.btn_test, self.btn_models, self.btn_disconnect):
            b.setEnabled(not on)
        if text:
            self.result.setText(text)
        if not on:
            self.reload()

    def save(self) -> bool:
        try:
            self.cm.save(self.pid, self.key.text().strip() or None, self.base_url.text().strip())
        except InvalidBaseURL as exc:
            self.result.setText(f"✖ {tr('conn.bad_url')}: {exc}")
            return False
        self.result.setText("✔ " + tr("conn.saved"))
        self.reload()
        self.changed.emit(self.pid)
        return True

    def _provider(self):
        typed = self.key.text().strip() or None
        try:
            return self.cm.provider(self.pid, typed, self.base_url.text().strip() or None)
        except InvalidBaseURL as exc:
            self.result.setText(f"✖ {tr('conn.bad_url')}: {exc}")
        except PermissionError:
            self.result.setText("✖ " + tr("conn.need_key"))
        return None

    def test(self) -> None:
        provider = self._provider()
        if provider is None:
            return
        self._busy(True, tr("conn.testing"))

        def call():
            # Trả lỗi như một giá trị để giữ nguyên loại lỗi (ProviderError.kind) khi về luồng UI
            try:
                return provider.list_models(), None
            except Exception as exc:
                return None, to_provider_error(exc)

        def finished(result) -> None:
            models, err = result
            if err is not None:
                self._busy(False)
                self.result.setText("✖ " + error_text(err))
                return
            if self.cm.is_connected(self.pid):
                self.cm.cache_models(self.pid, models)
            self._busy(False)
            self.result.setText("✔ " + tr("conn.test_ok", n=len(models)) +
                                ("" if self.cm.is_connected(self.pid) else "  " + tr("conn.test_ok_unsaved")))
            self.changed.emit(self.pid)

        run_in_background(call, finished, lambda msg: (self._busy(False), self.result.setText("✖ " + redact(msg)[:300])))

    def refresh_models(self) -> None:
        self.test()

    def disconnect(self) -> None:
        if QMessageBox.question(self, tr("conn.disconnect"), tr("conn.disconnect_q", name=self.meta.name)) \
                != QMessageBox.StandardButton.Yes:
            return
        self.cm.disconnect(self.pid)
        self.result.setText(tr("conn.disconnected"))
        self.reload()
        self.changed.emit(self.pid)


class ConnectionsDialog(QDialog):
    changed = Signal(str)

    def __init__(self, cm: ConnectionManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("conn.title"))
        self.resize(720, 760)
        lay = QVBoxLayout(self)
        note = label(tr("conn.note", backend=cm.secrets.backend_name), wrap=True)
        lay.addWidget(note)
        if not cm.secrets.persistent:
            lay.addWidget(badge(tr("conn.memory_only"), "warn"))
        area = QScrollArea()
        area.setWidgetResizable(True)
        host = QWidget()
        hl = QVBoxLayout(host)
        self.cards: dict[str, ProviderCard] = {}
        for pid in cm.provider_ids():
            card = ProviderCard(cm, pid)
            card.changed.connect(self.changed)
            self.cards[pid] = card
            hl.addWidget(card)
        hl.addStretch(1)
        area.setWidget(host)
        lay.addWidget(area, 1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
        lay.addWidget(bb)

