"""Tab AI Usage: tổng chi tiêu ước tính theo ngày/dự án/phiên so với ngân sách, ledger theo request,
và hộp thoại đặt ngân sách."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from app_builder.agent.budget import BudgetLimits, BudgetManager
from app_builder.core.i18n import tr
from app_builder.ui.widgets import label

SCOPE_KEYS = {"day": "usage.day", "project": "usage.project", "session": "usage.session"}


def fmt_money(v: float | None) -> str:
    return "—" if v is None else f"${v:.4f}"


class BudgetDialog(QDialog):
    def __init__(self, budget: BudgetManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.budget = budget
        self.setWindowTitle(tr("usage.budget_title"))
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.addWidget(label(tr("usage.budget_title"), "H2"))
        lim = budget.get_limits()
        form = QFormLayout()
        self.spins: dict[str, QDoubleSpinBox] = {}
        for key, val in (("daily_usd", lim.daily_usd), ("project_usd", lim.project_usd), ("session_usd", lim.session_usd)):
            sp = QDoubleSpinBox()
            sp.setRange(0, 10000)
            sp.setDecimals(2)
            sp.setPrefix("$ ")
            sp.setSpecialValueText(tr("usage.no_limit"))
            sp.setValue(val or 0)
            self.spins[key] = sp
            form.addRow(tr(f"usage.limit_{key}"), sp)
        lay.addLayout(form)
        lay.addWidget(label(tr("usage.budget_note"), "Muted", wrap=True))
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton(tr("common.cancel"))
        cancel.clicked.connect(self.reject)
        ok = QPushButton(tr("common.save"))
        ok.setObjectName("Primary")
        ok.clicked.connect(self._save)
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addLayout(row)

    def _save(self) -> None:
        self.budget.set_limits(BudgetLimits(**{k: (s.value() or None) for k, s in self.spins.items()}))
        self.accept()


class UsagePanel(QWidget):
    budget_changed = Signal()

    def __init__(self, budget: BudgetManager) -> None:
        super().__init__()
        self.budget = budget
        self.project_id: int | None = None
        self.overrides: BudgetLimits | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        top = QHBoxLayout()
        self.summary = label("", None, wrap=True)
        top.addWidget(self.summary, 1)
        btn = QPushButton(tr("usage.set_budget"))
        btn.clicked.connect(self._edit_budget)
        top.addWidget(btn)
        lay.addLayout(top)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([tr("usage.c_time"), "Provider", "Model", tr("usage.c_status"),
                                              "Input", "Cached", "Output", tr("usage.c_cost"), tr("usage.c_note")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table, 1)
        lay.addWidget(label(tr("usage.disclaimer", date=budget.prices.updated_on), "Muted", wrap=True))
        self.refresh()

    def set_project(self, project_id: int | None, overrides: BudgetLimits | None) -> None:
        self.project_id = project_id
        self.overrides = overrides
        self.refresh()

    def _edit_budget(self) -> None:
        if BudgetDialog(self.budget, self).exec():
            self.refresh()
            self.budget_changed.emit()

    def refresh(self) -> None:
        parts = []
        for sc in self.budget.scope_status(self.project_id, self.overrides):
            lim = f"${sc.limit:.2f}" if sc.limit else tr("usage.no_limit")
            s = f"{tr(SCOPE_KEYS[sc.scope])}: {fmt_money(sc.spent)} / {lim}"
            if sc.ratio is not None and sc.ratio >= 0.8:
                s = "⚠ " + s
            if sc.unknown_count:
                s += " " + tr("usage.unknown_n", n=sc.unknown_count)
            parts.append(s)
        self.summary.setText("   ·   ".join(parts))
        rows = self.budget.ledger(self.project_id)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            if r["cost_usd"] is not None:
                cost = fmt_money(r["cost_usd"])
            elif r["estimated_cost_usd"] is not None:
                cost = "≈" + fmt_money(r["estimated_cost_usd"]) + " " + tr("usage.est")
            else:
                cost = tr("assist.unknown")
            model = r["model"] + (f" → {r['served_model']}" if r["served_model"] and r["served_model"] != r["model"] else "")
            vals = [r["created_at"][:19].replace("T", " "), r["provider"], model, r["status"],
                    r["input_tokens"], r["cached_tokens"], r["output_tokens"], cost, r["note"]]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem("" if v is None else str(v)))
        self.table.resizeColumnsToContents()

    def badge_text(self) -> tuple[str, str]:
        """(text, kind) cho badge ngân sách trên toolbar."""
        sc = self.budget.scope_status(self.project_id, self.overrides)[0]
        if sc.limit:
            kind = "danger" if (sc.ratio or 0) >= 1 else ("warn" if (sc.ratio or 0) >= 0.8 else "ok")
            return tr("usage.badge_limit", spent=f"{sc.spent:.2f}", limit=f"{sc.limit:.2f}"), kind
        return tr("usage.badge", spent=f"{sc.spent:.2f}"), ""
