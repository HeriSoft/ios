"""Settings > Connections: thẻ cho từng provider — API key (ẩn/hiện), Base URL, Test Connection, Refresh Models,
chọn model (lọc theo khả năng), Disconnect. Key lưu trong Windows Credential Manager."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from app_builder.core.i18n import tr
from app_builder.providers.base import ModelInfo
from app_builder.providers.registry import BaseUrlError, ProviderRegistry, ProviderSpec, filter_models, validate_base_url, visible_specs
from app_builder.ui.async_runner import AsyncCall
from app_builder.ui.widgets import MilestoneNotice, badge, label, set_badge_kind

STATUS_KIND = {"authenticated": ("ok", "conn.st_ok"), "auth_failed": ("danger", "conn.st_auth"),
               "network": ("warn", "conn.st_network"), "error": ("danger", "conn.st_error"),
               "not_configured": ("", "conn.st_none")}


class ProviderCard(QFrame):
    changed = Signal()

    def __init__(self, spec: ProviderSpec, registry: ProviderRegistry) -> None:
        super().__init__()
        self.spec = spec
        self.reg = registry
        self.models: list[ModelInfo] = []
        self._call: AsyncCall | None = None
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        head = QHBoxLayout()
        head.addWidget(label(spec.name, "H2"))
        head.addStretch(1)
        self.status = badge("")
        head.addWidget(self.status)
        lay.addLayout(head)
        lay.addWidget(label(spec.note, "Muted", wrap=True))

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        row = 0
        if not spec.test_only:
            self.key = QLineEdit()
            self.key.setEchoMode(QLineEdit.EchoMode.Password)
            self.key.setPlaceholderText(spec.key_hint)
            self.btn_eye = QPushButton("👁")
            self.btn_eye.setCheckable(True)
            self.btn_eye.setFixedWidth(36)
            self.btn_eye.setToolTip(tr("conn.show"))
            self.btn_eye.toggled.connect(lambda on: self.key.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
            self.btn_save = QPushButton(tr("conn.save_key"))
            self.btn_save.clicked.connect(self.save_key)
            grid.addWidget(label("API key"), row, 0)
            grid.addWidget(self.key, row, 1)
            grid.addWidget(self.btn_eye, row, 2)
            grid.addWidget(self.btn_save, row, 3)
            row += 1
            if spec.key_url:
                link = QPushButton(tr("conn.get_key"))
                link.setObjectName("Flat")
                link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(spec.key_url)))
                grid.addWidget(link, row, 1, 1, 1, Qt.AlignmentFlag.AlignLeft)
                row += 1
        self.base_url = QLineEdit()
        self.base_url.setPlaceholderText(spec.default_base_url or tr("conn.official_only"))
        self.base_url.setEnabled(spec.allows_custom_base_url)
        self.base_url.textChanged.connect(self._url_changed)
        grid.addWidget(label("Base URL"), row, 0)
        grid.addWidget(self.base_url, row, 1, 1, 3)
        row += 1
        self.url_warn = label("", "Muted", wrap=True)
        self.url_warn.setStyleSheet("color: #F5B94A;")
        grid.addWidget(self.url_warn, row, 1, 1, 3)
        row += 1
        lay.addLayout(grid)

        btns = QHBoxLayout()
        self.btn_test = QPushButton(tr("conn.test"))
        self.btn_test.clicked.connect(self.test)
        self.btn_models = QPushButton(tr("conn.refresh_models"))
        self.btn_models.clicked.connect(self.refresh_models)
        self.btn_disconnect = QPushButton(tr("conn.disconnect"))
        self.btn_disconnect.setObjectName("Danger")
        self.btn_disconnect.clicked.connect(self.do_disconnect)
        btns.addWidget(self.btn_test)
        btns.addWidget(self.btn_models)
        btns.addStretch(1)
        btns.addWidget(self.btn_disconnect)
        lay.addLayout(btns)

        mrow = QHBoxLayout()
        mrow.addWidget(label(tr("conn.model")))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(320)
        self.model_combo.activated.connect(self._model_chosen)
        mrow.addWidget(self.model_combo, 1)
        lay.addLayout(mrow)
        frow = QHBoxLayout()
        frow.addWidget(label(tr("conn.filter"), "Muted"))
        self.filters: dict[str, QCheckBox] = {}
        for cap in ("vision", "tools", "structured", "reasoning"):
            cb = QCheckBox(tr(f"conn.cap.{cap}"))
            cb.toggled.connect(self._fill_models)
            self.filters[cap] = cb
            frow.addWidget(cb)
        self.include_unknown = QCheckBox(tr("conn.include_unknown"))
        self.include_unknown.setChecked(True)
        self.include_unknown.toggled.connect(self._fill_models)
        frow.addWidget(self.include_unknown)
        frow.addStretch(1)
        lay.addLayout(frow)
        self.model_info = label("", "Muted", wrap=True)
        lay.addWidget(self.model_info)
        if spec.id == "anthropic":
            self.cb_fallback = QCheckBox(tr("conn.refusal_fallback"))
            self.cb_fallback.setToolTip(tr("conn.refusal_fallback_tip"))
            self.cb_fallback.toggled.connect(self._fallback_toggled)
            lay.addWidget(self.cb_fallback)
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        cfg = self.reg.get_config(self.spec.id)
        if self.spec.allows_custom_base_url:
            self.base_url.blockSignals(True)
            self.base_url.setText(cfg.base_url if cfg.base_url != self.spec.default_base_url else "")
            self.base_url.blockSignals(False)
        has_key = self.reg.has_api_key(self.spec.id)
        if not self.spec.test_only:
            self.key.setPlaceholderText(self.reg.masked_key(self.spec.id) if has_key else self.spec.key_hint)
        kind, key = STATUS_KIND.get(cfg.status, ("", "conn.st_none"))
        text = tr(key) if has_key or self.spec.test_only else tr("conn.st_nokey")
        set_badge_kind(self.status, text, kind if has_key or self.spec.test_only else "")
        self.status.setToolTip(cfg.status_message)
        self.models, fetched = self.reg.cached_models(self.spec.id)
        self._fill_models()
        if fetched:
            self.model_info.setText(self.model_info.text() + "\n" + tr("conn.cached_at", time=fetched))
        for b in (self.btn_test, self.btn_models, self.btn_disconnect):
            b.setEnabled(has_key or self.spec.test_only)
        if self.spec.id == "anthropic":
            self.cb_fallback.blockSignals(True)
            self.cb_fallback.setChecked(bool(cfg.options.get("refusal_fallback", True)))
            self.cb_fallback.blockSignals(False)

    def _url_changed(self, text: str) -> None:
        try:
            _, custom, warn = validate_base_url(self.spec, text)
            self.url_warn.setText(warn)
        except BaseUrlError as exc:
            self.url_warn.setText("✖ " + str(exc))

    def _fill_models(self) -> None:
        req = {c for c, cb in self.filters.items() if cb.isChecked()}
        shown = filter_models(self.models, req, self.include_unknown.isChecked())
        cfg = self.reg.get_config(self.spec.id)
        self.model_combo.clear()
        if not shown:
            self.model_combo.addItem(tr("conn.no_models") if not self.models else tr("conn.no_match"), "")
        for m in shown:
            flags = "".join(("✓" if m.capabilities.get(c) else ("?" if m.capabilities.get(c) is None else "·"))
                            for c in ("vision", "tools", "structured", "reasoning"))
            self.model_combo.addItem(f"{m.label()}   [{flags}]" + ("  ⚠ deprecated" if m.deprecated else ""), m.id)
        idx = self.model_combo.findData(cfg.selected_model) if cfg.selected_model else -1
        if idx < 0 and self.spec.default_model:
            idx = self.model_combo.findData(self.spec.default_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        sel = next((m for m in self.models if m.id == self.model_combo.currentData()), None)
        info = tr("conn.flags_legend")
        if sel:
            info += "\n" + tr("conn.model_meta", ctx=sel.context_window or "?", out=sel.max_output or "?")
        if cfg.status_message and "không còn" in cfg.status_message:
            info += "\n⚠ " + cfg.status_message
        self.model_info.setText(info)
        if not cfg.selected_model and self.model_combo.currentData():
            self.reg.select_model(self.spec.id, self.model_combo.currentData())

    def _model_chosen(self, _idx: int) -> None:
        mid = self.model_combo.currentData()
        if mid:
            self.reg.select_model(self.spec.id, mid)
            self._fill_models()
            self.changed.emit()

    def _fallback_toggled(self, on: bool) -> None:
        cfg = self.reg.get_config(self.spec.id)
        cfg.options["refusal_fallback"] = on
        self.reg.save_config(cfg)

    def _busy(self, busy: bool, text: str = "") -> None:
        for b in (self.btn_test, self.btn_models, self.btn_disconnect):
            b.setEnabled(not busy)
        if busy:
            set_badge_kind(self.status, text, "warn")

    # ---- actions ----------------------------------------------------------
    def save_key(self) -> None:
        key = self.key.text().strip()
        if not key:
            QMessageBox.information(self, self.spec.name, tr("conn.enter_key"))
            return
        try:
            _, custom, warn = validate_base_url(self.spec, self.base_url.text())
            if custom and QMessageBox.question(self, self.spec.name, warn + "\n\n" + tr("conn.custom_confirm")) \
                    != QMessageBox.StandardButton.Yes:
                return
            self.reg.set_api_key(self.spec.id, key, self.base_url.text() or None)
        except (BaseUrlError, ValueError) as exc:
            QMessageBox.warning(self, self.spec.name, str(exc))
            return
        self.key.clear()
        if not self.reg.secrets.persistent:
            QMessageBox.warning(self, self.spec.name, tr("conn.memory_only"))
        self.load()
        self.test()

    def test(self) -> None:
        try:
            provider = self.reg.create(self.spec.id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, self.spec.name, str(exc))
            return
        self._busy(True, tr("conn.testing"))

        async def work():
            res = await provider.test_connection()
            models = await provider.list_models() if res.ok else []
            return res, models

        def done(out):
            res, models = out
            self.reg.record_status(self.spec.id, res.status, res.message)
            if res.ok:
                self.reg.save_models(self.spec.id, models)
            self.load()
            if res.ok:
                self.status.setToolTip(tr("conn.ok_detail", n=res.model_count or 0, ms=res.latency_ms or 0))
            else:
                QMessageBox.warning(self, self.spec.name, res.message)
            self.changed.emit()

        def fail(msg: str):
            self.reg.record_status(self.spec.id, "error", msg)
            self.load()
            QMessageBox.warning(self, self.spec.name, msg)

        self._call = AsyncCall(work(), done, fail, self)

    def refresh_models(self) -> None:
        try:
            provider = self.reg.create(self.spec.id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, self.spec.name, str(exc))
            return
        self._busy(True, tr("conn.loading_models"))

        def done(models):
            self.reg.save_models(self.spec.id, models)
            self.reg.record_status(self.spec.id, "authenticated", "")
            self.load()
            self.changed.emit()

        def fail(msg: str):
            self.load()
            QMessageBox.warning(self, self.spec.name, msg)

        self._call = AsyncCall(provider.list_models(), done, fail, self)

    def do_disconnect(self) -> None:
        if QMessageBox.question(self, self.spec.name, tr("conn.disconnect_confirm", name=self.spec.name)) \
                != QMessageBox.StandardButton.Yes:
            return
        self.reg.disconnect(self.spec.id)
        self.load()
        self.changed.emit()


class ConnectionsDialog(QDialog):
    changed = Signal()

    def __init__(self, registry: ProviderRegistry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("conn.title"))
        self.resize(900, 760)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.addWidget(label(tr("conn.title"), "H2"))
        lay.addWidget(label(tr("conn.sub"), "Muted", wrap=True))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        v = QVBoxLayout(host)
        v.setSpacing(12)
        self.cards: list[ProviderCard] = []
        for spec in visible_specs():
            card = ProviderCard(spec, registry)
            card.changed.connect(self.changed.emit)
            self.cards.append(card)
            v.addWidget(card)
        v.addWidget(MilestoneNotice(tr("conn.claude_code"), "M7", tr("conn.claude_code_notice")))
        v.addWidget(MilestoneNotice(tr("conn.claude_desktop"), "M7", tr("conn.claude_desktop_notice")))
        v.addStretch(1)
        scroll.setWidget(host)
        lay.addWidget(scroll, 1)
        row = QHBoxLayout()
        row.addWidget(label(tr("conn.storage", backend=registry.secrets.backend_name), "Muted"), 1)
        close = QPushButton(tr("common.close"))
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)
