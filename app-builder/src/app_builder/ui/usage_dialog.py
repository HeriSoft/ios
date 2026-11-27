"""Hộp thoại Chi phí AI: tổng đã dùng, ngân sách phiên, lịch sử request, bảng giá (có nguồn + ngày)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from app_builder.agent.budget import BUILTIN_PRICES, BudgetManager, Price
from app_builder.core.i18n import tr
from app_builder.providers.base import REAL_PROVIDERS
from app_builder.ui.widgets import label


def usd(v: float | None, approx: bool = False) -> str:
    if v is None:
        return "?"
    # ≥ $1: 2 chữ số thập phân; số nhỏ (chi phí từng lượt) cần 4 chữ số
    text = f"${v:,.2f}" if abs(v) >= 1 else f"${v:,.4f}"
    return ("≈ " if approx else "") + text.replace(",", " ").replace(".", ",")


def _ro(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return it


class UsageDialog(QDialog):
    def __init__(self, budget: BudgetManager, project_id: int | None = None, project_limit: float | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.budget, self.project_id, self.project_limit = budget, project_id, project_limit
        self.setWindowTitle(tr("usage.title"))
        self.resize(860, 640)
        lay = QVBoxLayout(self)
        self.summary = label("", wrap=True)
        lay.addWidget(self.summary)

        brow = QHBoxLayout()
        brow.addWidget(label(tr("usage.session_budget")))
        self.session_budget = QDoubleSpinBox()
        self.session_budget.setRange(0, 10_000)
        self.session_budget.setDecimals(2)
        self.session_budget.setPrefix("$ ")
        self.session_budget.setSpecialValueText(tr("usage.no_limit"))
        self.session_budget.setValue(budget.session_limit() or 0)
        brow.addWidget(self.session_budget)
        save_b = QPushButton(tr("common.save"))
        save_b.clicked.connect(self._save_budget)
        brow.addWidget(save_b)
        brow.addStretch(1)
        lay.addLayout(brow)

        tabs = QTabWidget()
        lay.addWidget(tabs, 1)
        self.history = QTableWidget(0, 8)
        self.history.setHorizontalHeaderLabels([tr("usage.col_time"), "Provider", "Model", tr("usage.col_in"),
                                                tr("usage.col_cached"), tr("usage.col_out"), tr("usage.col_cost"),
                                                tr("usage.col_status")])
        self.history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tabs.addTab(self.history, tr("usage.history"))

        prices = QWidget()
        pl = QVBoxLayout(prices)
        pl.addWidget(label(tr("usage.prices_note"), wrap=True))
        self.prices = QTableWidget(0, 7)
        self.prices.setHorizontalHeaderLabels(["Provider", "Model", tr("usage.p_in"), tr("usage.p_cached"),
                                               tr("usage.p_out"), tr("usage.p_source"), tr("usage.p_updated")])
        self.prices.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        pl.addWidget(self.prices, 1)
        form = QFormLayout()
        self.p_provider = QComboBox()
        for p in REAL_PROVIDERS:
            self.p_provider.addItem(p.name, p.id)
        self.p_model = QLineEdit()
        self.p_model.setPlaceholderText(tr("usage.p_model_ph"))
        self.p_in, self.p_out, self.p_cached = (QDoubleSpinBox() for _ in range(3))
        for sb in (self.p_in, self.p_out, self.p_cached):
            sb.setRange(0, 1000)
            sb.setDecimals(4)
            sb.setPrefix("$ ")
        self.p_cached.setSpecialValueText(tr("usage.p_cached_same"))
        form.addRow("Provider", self.p_provider)
        form.addRow("Model", self.p_model)
        form.addRow(tr("usage.p_in"), self.p_in)
        form.addRow(tr("usage.p_out"), self.p_out)
        form.addRow(tr("usage.p_cached"), self.p_cached)
        prow = QHBoxLayout()
        self.p_save = QPushButton(tr("usage.p_save"))
        self.p_delete = QPushButton(tr("usage.p_delete"))
        self.p_save.clicked.connect(self._save_price)
        self.p_delete.clicked.connect(self._delete_price)
        prow.addWidget(self.p_save)
        prow.addWidget(self.p_delete)
        prow.addStretch(1)
        pl.addLayout(form)
        pl.addLayout(prow)
        self.price_status = label("")
        pl.addWidget(self.price_status)
        tabs.addTab(prices, tr("usage.prices"))

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.refresh()

    def refresh(self) -> None:
        b = self.budget
        limit = b.session_limit()
        parts = [tr("usage.sum_session", spent=usd(b.spent_session()), limit=usd(limit) if limit else tr("usage.no_limit"))]
        if self.project_id is not None:
            parts.append(tr("usage.sum_project", spent=usd(b.spent_project(self.project_id)),
                            limit=usd(self.project_limit) if self.project_limit else tr("usage.no_limit")))
        parts.append(tr("usage.sum_total", spent=usd(b.spent_total())))
        self.summary.setText("   ·   ".join(parts))

        rows = b.recent()
        self.history.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r["created_at"].replace("T", " ")[:19], r["provider"], r["model"], str(r["input_tokens"] or 0),
                    str(r["cached_tokens"] or 0), str(r["output_tokens"] or 0),
                    usd(r["cost_usd"], approx=bool(r["cost_usd"] is not None and not r["cost_known"])), r["status"]]
            for j, v in enumerate(vals):
                self.history.setItem(i, j, _ro(v))

        table = dict(BUILTIN_PRICES)
        table.update(b.prices.user_prices())
        items = sorted((k, v) for k, v in table.items() if k[0] != "fake")
        self.prices.setRowCount(len(items))
        for i, ((prov, model), p) in enumerate(items):
            vals = [prov, model, f"{p.input_per_m:g}", "—" if p.cached_input_per_m is None else f"{p.cached_input_per_m:g}",
                    f"{p.output_per_m:g}", p.source, p.updated]
            for j, v in enumerate(vals):
                self.prices.setItem(i, j, _ro(v))

    def _save_budget(self) -> None:
        self.budget.set_session_limit(self.session_budget.value() or None)
        self.refresh()

    def _save_price(self) -> None:
        model = self.p_model.text().strip()
        if not model or self.p_out.value() <= 0 and self.p_in.value() <= 0:
            self.price_status.setText("✖ " + tr("usage.p_invalid"))
            return
        cached = self.p_cached.value() or None
        self.budget.prices.set_user_price(self.p_provider.currentData(), model,
                                          Price(self.p_in.value(), self.p_out.value(), cached))
        self.price_status.setText("✔ " + tr("usage.p_saved"))
        self.refresh()

    def _delete_price(self) -> None:
        self.budget.prices.set_user_price(self.p_provider.currentData(), self.p_model.text().strip(), None)
        self.refresh()
