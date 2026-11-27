"""Ngân sách AI local: bảng giá có ngày cập nhật, ước lượng trước request, ledger usage, cảnh báo 80%,
chặn request mới khi vượt ngưỡng, reservation cho request đang chạy.

Đây là giới hạn ƯỚC LƯỢNG phía máy bạn, không bảo đảm khớp hóa đơn (retry, usage trễ, làm tròn, giá thay đổi).
Hãy đặt thêm giới hạn chi tiêu trên trang của provider nếu có.
"""
from __future__ import annotations

import json
import math
import threading
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from app_builder.core.config import resources_dir
from app_builder.core.database import Database
from app_builder.core.schemas import utcnow_iso
from app_builder.providers.base import AIRequest, Usage

IMAGE_TOKEN_ESTIMATE = 1600
WARN_RATIO = 0.8


@dataclass
class Price:
    input: float
    output: float
    cached_input: float | None = None  # None => tính cached theo giá input (ước lượng cao)
    max_prompt_tokens: int | None = None

    def cost(self, usage: Usage) -> float | None:
        if usage.input_tokens is None or usage.output_tokens is None:
            return None
        if self.max_prompt_tokens and usage.input_tokens > self.max_prompt_tokens:
            return None
        cached = min(usage.cached_input_tokens or 0, usage.input_tokens)
        cached_price = self.cached_input if self.cached_input is not None else self.input
        return ((usage.input_tokens - cached) * self.input + cached * cached_price
                + usage.output_tokens * self.output) / 1_000_000


class PriceTable:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.updated_on: str = data.get("updated_on", "?")
        self.sources: dict = data.get("sources", {})

    @classmethod
    def load(cls, path: Path | None = None) -> "PriceTable":
        p = path or (resources_dir() / "pricing.json")
        return cls(json.loads(Path(p).read_text("utf-8")))

    def price_for(self, provider: str, model: str, prompt_tokens: int = 0, on: date | None = None) -> Price | None:
        entries = self.data.get("providers", {}).get(provider, {}).get(model.removeprefix("models/"))
        if not entries:
            return None
        today = (on or datetime.now(timezone.utc).date()).isoformat()
        valid = [e for e in entries if (e.get("effective_from") or "") <= today]
        # Sắp theo (ngưỡng prompt, ngày hiệu lực): mục cuối thỏa điều kiện = bậc cao nhất áp dụng, giá mới nhất
        chosen = None
        for e in sorted(valid, key=lambda e: (e.get("prompt_tokens_above", 0), e.get("effective_from") or "")):
            above = e.get("prompt_tokens_above", 0)
            if above == 0 or prompt_tokens > above:
                chosen = e
        if chosen is None:
            return None
        return Price(chosen["input"], chosen["output"], chosen.get("cached_input"), chosen.get("max_prompt_tokens"))


def estimate_tokens(text: str) -> int:
    """Ước lượng THẬN TRỌNG (dư): ~1 token / 3 byte UTF-8 (tiếng Việt có dấu tốn nhiều byte hơn)."""
    return math.ceil(len(text.encode("utf-8")) / 3) + 4


def estimate_request_tokens(req: AIRequest) -> int:
    n = estimate_tokens(req.system)
    for m in req.messages:
        n += estimate_tokens(m.text) + IMAGE_TOKEN_ESTIMATE * len(m.images)
    for f in req.context_files:
        n += estimate_tokens(f.path) + estimate_tokens(f.content) + 10
    return n


@dataclass
class BudgetLimits:
    daily_usd: float | None = None
    project_usd: float | None = None
    session_usd: float | None = None


@dataclass
class ScopeStatus:
    scope: str
    limit: float | None
    spent: float
    reserved: float
    unknown_count: int = 0

    @property
    def ratio(self) -> float | None:
        if not self.limit:
            return None
        return (self.spent + self.reserved) / self.limit


@dataclass
class BudgetDecision:
    status: str  # ok | warn | blocked | unknown_price
    estimate_usd: float | None
    input_tokens_est: int
    max_output_tokens: int
    price: Price | None
    scopes: list[ScopeStatus] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    @property
    def allowed_without_confirm(self) -> bool:
        return self.status in ("ok", "warn")


class BudgetManager:
    def __init__(self, db: Database, prices: PriceTable | None = None, session_id: str | None = None) -> None:
        self.db = db
        self.prices = prices or PriceTable.load()
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self._reservations: dict[str, tuple[float, int | None]] = {}
        self._lock = threading.Lock()

    # ---- limits ---------------------------------------------------------------
    def get_limits(self) -> BudgetLimits:
        r = self.db.query_one("SELECT value FROM settings WHERE key='budget_limits'")
        if r:
            try:
                return BudgetLimits(**json.loads(r["value"]))
            except (TypeError, json.JSONDecodeError):
                pass
        return BudgetLimits()

    def set_limits(self, limits: BudgetLimits) -> None:
        for v in (limits.daily_usd, limits.project_usd, limits.session_usd):
            if v is not None and v < 0:
                raise ValueError("Ngân sách không được âm")
        self.db.execute("INSERT INTO settings(key, value) VALUES('budget_limits', ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (json.dumps(limits.__dict__),))

    # ---- spent ------------------------------------------------------------------
    def _sum(self, where: str, params: tuple) -> tuple[float, int]:
        r = self.db.query_one(
            "SELECT COALESCE(SUM(COALESCE(cost_usd, estimated_cost_usd, 0)), 0) AS s, "
            "SUM(CASE WHEN cost_usd IS NULL THEN 1 ELSE 0 END) AS unknown FROM usage_records WHERE " + where, params)
        return float(r["s"] or 0), int(r["unknown"] or 0)

    def spent_today(self) -> tuple[float, int]:
        start = datetime.now(timezone.utc).date().isoformat()
        return self._sum("created_at >= ?", (start,))

    def spent_project(self, project_id: int | None) -> tuple[float, int]:
        return self._sum("project_id IS ?", (project_id,))

    def spent_session(self) -> tuple[float, int]:
        return self._sum("session_id = ?", (self.session_id,))

    def reserved(self, project_id: int | None = None, scope: str = "all") -> float:
        with self._lock:
            if scope == "project":
                return sum(v for v, pid in self._reservations.values() if pid == project_id)
            return sum(v for v, _ in self._reservations.values())

    def effective_limits(self, overrides: BudgetLimits | None = None) -> BudgetLimits:
        """Giới hạn toàn cục, ghi đè bởi giới hạn riêng của project (spec.ai) nếu có."""
        lim = self.get_limits()
        if overrides:
            for k in ("daily_usd", "project_usd", "session_usd"):
                v = getattr(overrides, k)
                if v:
                    setattr(lim, k, v)
        return lim

    def scope_status(self, project_id: int | None, overrides: BudgetLimits | None = None) -> list[ScopeStatus]:
        lim = self.effective_limits(overrides)
        d, du = self.spent_today()
        p, pu = self.spent_project(project_id)
        s, su = self.spent_session()
        return [ScopeStatus("day", lim.daily_usd, d, self.reserved(), du),
                ScopeStatus("project", lim.project_usd, p, self.reserved(project_id, "project"), pu),
                ScopeStatus("session", lim.session_usd, s, self.reserved(), su)]

    # ---- check / reserve / record ---------------------------------------------------
    def check(self, provider: str, req: AIRequest, project_id: int | None = None,
              overrides: BudgetLimits | None = None) -> BudgetDecision:
        tokens = estimate_request_tokens(req)
        price = self.prices.price_for(provider, req.model, tokens)
        estimate = None
        if price and not (price.max_prompt_tokens and tokens > price.max_prompt_tokens):
            estimate = (tokens * price.input + req.max_output_tokens * price.output) / 1_000_000
        scopes = self.scope_status(project_id, overrides)
        names = {"day": "hôm nay", "project": "dự án", "session": "phiên"}
        msgs: list[str] = []
        status = "ok"
        for sc in scopes:
            if not sc.limit:
                continue
            projected = sc.spent + sc.reserved + (estimate or 0)
            if projected > sc.limit:
                status = "blocked"
                msgs.append(f"Vượt ngân sách {names[sc.scope]}: đã dùng ${sc.spent:.4f} + đang chạy ${sc.reserved:.4f}"
                            f" + ước tính ${estimate or 0:.4f} > ${sc.limit:.2f}")
            elif projected >= WARN_RATIO * sc.limit and status != "blocked":
                status = "warn"
                msgs.append(f"Đã dùng ≥80% ngân sách {names[sc.scope]} (${projected:.4f}/${sc.limit:.2f}).")
        if estimate is None and status != "blocked":
            status = "unknown_price"
            msgs.append(f"Chưa có giá cho model '{req.model}' (bảng giá cập nhật {self.prices.updated_on}) "
                        "— chi phí KHÔNG xác định, cần bạn xác nhận.")
        return BudgetDecision(status, estimate, tokens, req.max_output_tokens, price, scopes, msgs)

    def reserve(self, request_id: str, estimate: float | None, project_id: int | None = None) -> None:
        with self._lock:
            self._reservations[request_id] = (estimate or 0.0, project_id)

    def release(self, request_id: str) -> None:
        with self._lock:
            self._reservations.pop(request_id, None)

    def record(self, *, request_id: str, provider: str, model: str, usage: Usage | None, status: str,
               project_id: int | None = None, estimate: float | None = None, note: str = "") -> float | None:
        """Ghi usage thực tế. Giá unknown => cost_usd NULL (không ghi $0). Request bị dừng/lỗi không rõ usage =>
        giữ ước tính để ngân sách thận trọng."""
        cost: float | None = None
        served = usage.served_model if usage else None
        if usage and usage.input_tokens is not None:
            price = self.prices.price_for(provider, served or model, usage.input_tokens)
            cost = price.cost(usage) if price else None
        self.db.execute(
            "INSERT INTO usage_records(project_id, provider, model, request_id, input_tokens, output_tokens, cached_tokens,"
            " reasoning_tokens, cost_usd, cost_known, status, created_at, session_id, estimated_cost_usd, served_model, note)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (project_id, provider, model, request_id,
             usage.input_tokens if usage else None, usage.output_tokens if usage else None,
             usage.cached_input_tokens if usage else None, usage.reasoning_tokens if usage else None,
             cost, int(cost is not None), status, utcnow_iso(), self.session_id,
             estimate if cost is None else None, served, note),
        )
        self.release(request_id)
        return cost

    def ledger(self, project_id: int | None = None, limit: int = 200) -> list:
        if project_id is None:
            return self.db.query("SELECT * FROM usage_records ORDER BY id DESC LIMIT ?", (limit,))
        return self.db.query("SELECT * FROM usage_records WHERE project_id IS ? ORDER BY id DESC LIMIT ?",
                             (project_id, limit))
