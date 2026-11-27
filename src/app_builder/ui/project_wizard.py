"""Wizard tạo project 5 bước (mục 3.1)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
    QPushButton, QRadioButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from app_builder.core.i18n import language, tr
from app_builder.core.schemas import AIPreferences, CapabilitySpec, ProjectSpec, ThemeSpec
from app_builder.core.workspace import is_valid_android_package, is_valid_ios_bundle_id, package_id_from, slugify
from app_builder.services.project_service import ProjectError, ProjectService
from app_builder.services.template_service import CATEGORIES, UI_STYLES
from app_builder.ui.widgets import MilestoneNotice, badge, label, run_in_background

MAX_REF_BYTES = 5 * 1024 * 1024
REF_FILTER = "Ảnh / văn bản (*.png *.jpg *.jpeg *.txt *.md)"
PROVIDERS = [("openai", "OpenAI (ChatGPT API)"), ("deepseek", "DeepSeek"), ("gemini", "Google Gemini"),
             ("anthropic", "Claude API (Anthropic)"), ("claude_code", "Claude Code (local CLI)")]


def _set_invalid(w: QWidget, bad: bool) -> None:
    w.setProperty("invalid", "true" if bad else "false")
    w.style().unpolish(w)
    w.style().polish(w)


def _page(title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    inner = QWidget()
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(28, 22, 28, 22)
    lay.setSpacing(12)
    lay.addWidget(label(title, "H2"))
    lay.addWidget(label(subtitle, "Muted", wrap=True))
    scroll.setWidget(inner)
    return scroll, lay


class ProjectWizard(QDialog):
    def __init__(self, projects: ProjectService, default_parent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.projects = projects
        self.templates = projects.templates
        self.created_id: int | None = None
        self._pkg_touched = False
        self._bid_touched = False
        self.references: list[Path] = []
        self.setWindowTitle(tr("wiz.title"))
        self.setMinimumSize(980, 660)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        side = QFrame()
        side.setObjectName("Panel")
        side.setFixedWidth(230)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(14, 20, 14, 14)
        sv.addWidget(label(tr("wiz.title"), "H3"))
        self.steps = QListWidget()
        self.steps.setObjectName("StepList")
        for i, key in enumerate(("wiz.s1", "wiz.s2", "wiz.s3", "wiz.s4", "wiz.s5"), 1):
            self.steps.addItem(f"{i}.  {tr(key)}")
        self.steps.currentRowChanged.connect(self._go)
        sv.addWidget(self.steps, 1)
        root.addWidget(side)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        right.addWidget(self.stack, 1)
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 10, 20, 16)
        self.error_label = label("", "Muted", wrap=True)
        self.error_label.setStyleSheet("color: #F2668B;")
        footer.addWidget(self.error_label, 1)
        self.btn_back = QPushButton(tr("wiz.back"))
        self.btn_back.clicked.connect(lambda: self._go(self.stack.currentIndex() - 1))
        self.btn_next = QPushButton(tr("wiz.next"))
        self.btn_next.setObjectName("Primary")
        self.btn_next.clicked.connect(self._next)
        self.btn_cancel = QPushButton(tr("common.cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_back)
        footer.addWidget(self.btn_next)
        right.addLayout(footer)
        host = QWidget()
        host.setLayout(right)
        root.addWidget(host, 1)

        self._build_step1(default_parent)
        self._build_step2()
        self._build_step3()
        self._build_step4()
        self._build_step5()
        self.steps.setCurrentRow(0)

    # ---- Step 1 ---------------------------------------------------------------
    def _build_step1(self, default_parent: str) -> None:
        page, lay = _page(tr("wiz.s1.title"), tr("wiz.s1.sub"))
        form = QFormLayout()
        form.setSpacing(10)
        self.name = QLineEdit()
        self.name.setPlaceholderText(tr("wiz.name_ph"))
        self.name.setMaxLength(60)
        self.name.textChanged.connect(self._name_changed)
        self.desc = QPlainTextEdit()
        self.desc.setPlaceholderText(tr("wiz.desc_ph"))
        self.desc.setFixedHeight(70)
        self.pkg = QLineEdit()
        self.pkg.textEdited.connect(lambda _: setattr(self, "_pkg_touched", True))
        self.pkg.textChanged.connect(self._validate_ids)
        self.bid = QLineEdit()
        self.bid.textEdited.connect(lambda _: setattr(self, "_bid_touched", True))
        self.bid.textChanged.connect(self._validate_ids)
        dir_row = QHBoxLayout()
        self.parent_dir = QLineEdit(default_parent)
        self.parent_dir.textChanged.connect(self._update_dest)
        browse = QPushButton(tr("wiz.browse"))
        browse.clicked.connect(self._browse)
        dir_row.addWidget(self.parent_dir, 1)
        dir_row.addWidget(browse)
        self.dest_label = label("", "Muted", wrap=True)
        self.lang = QComboBox()
        self.lang.addItem("Tiếng Việt", "vi")
        self.lang.addItem("English", "en")
        if language() == "en":
            self.lang.setCurrentIndex(1)
        plat = QHBoxLayout()
        self.cb_android = QCheckBox("Android")
        self.cb_android.setChecked(True)
        self.cb_ios = QCheckBox("iOS")
        self.cb_ios.setChecked(True)
        plat.addWidget(self.cb_android)
        plat.addWidget(self.cb_ios)
        plat.addStretch(1)
        form.addRow(tr("wiz.name"), self.name)
        form.addRow(tr("wiz.desc"), self.desc)
        form.addRow(tr("wiz.pkg"), self.pkg)
        form.addRow(tr("wiz.bid"), self.bid)
        form.addRow(tr("wiz.parent"), dir_row)
        form.addRow("", self.dest_label)
        form.addRow(tr("wiz.lang"), self.lang)
        form.addRow(tr("wiz.platforms"), plat)
        lay.addLayout(form)
        lay.addWidget(label(tr("wiz.ios_note"), "Muted", wrap=True))
        lay.addStretch(1)
        self.stack.addWidget(page)

    def _name_changed(self, text: str) -> None:
        pkg = package_id_from(text or "my app")
        if not self._pkg_touched:
            self.pkg.setText(pkg)
        if not self._bid_touched:
            self.bid.setText(pkg)
        self._update_dest()

    def _validate_ids(self) -> None:
        _set_invalid(self.pkg, not is_valid_android_package(self.pkg.text()))
        _set_invalid(self.bid, not is_valid_ios_bundle_id(self.bid.text()))

    def _dest(self) -> Path:
        return Path(self.parent_dir.text().strip() or ".") / slugify(self.name.text() or "my-app")

    def _update_dest(self) -> None:
        d = self._dest()
        msg = tr("wiz.dest", path=str(d))
        if d.exists() and any(d.iterdir()):
            msg += "  ⚠ " + tr("wiz.dest_exists")
        self.dest_label.setText(msg)

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, tr("wiz.parent"), self.parent_dir.text())
        if d:
            self.parent_dir.setText(d)

    # ---- Step 2 ---------------------------------------------------------------
    def _build_step2(self) -> None:
        page, lay = _page(tr("wiz.s2.title"), tr("wiz.s2.sub"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.cat_buttons: dict[str, QPushButton] = {}
        lang = language()
        for i, c in enumerate(CATEGORIES):
            b = QPushButton(c[lang] if lang in c else c["vi"])
            b.setObjectName("CategoryChip")
            b.setCheckable(True)
            b.setToolTip(c["hint_vi"])
            b.toggled.connect(self._categories_changed)
            self.cat_buttons[c["id"]] = b
            grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(grid)
        lay.addSpacing(6)
        row = QHBoxLayout()
        row.addWidget(label(tr("wiz.template"), "H3"))
        self.template_combo = QComboBox()
        for t in self.templates.list_templates():
            self.template_combo.addItem(t.label(lang), t.id)
        self.template_combo.currentIndexChanged.connect(self._template_changed)
        row.addWidget(self.template_combo, 1)
        lay.addLayout(row)
        self.template_desc = label("", "Muted", wrap=True)
        lay.addWidget(self.template_desc)
        self.category_note = label("", "Muted", wrap=True)
        lay.addWidget(self.category_note)
        lay.addWidget(label(tr("wiz.features"), "H3"))
        self.features = QPlainTextEdit()
        self.features.setPlaceholderText(tr("wiz.features_ph"))
        self.features.setFixedHeight(80)
        lay.addWidget(self.features)
        lay.addWidget(label(tr("wiz.style"), "H3"))
        style_row = QHBoxLayout()
        self.style_group = QButtonGroup(self)
        for i, (sid, s) in enumerate(UI_STYLES.items()):
            rb = QRadioButton(s.get(lang, s["vi"]))
            rb.setProperty("style_id", sid)
            sw = QLabel()
            sw.setFixedSize(28, 18)
            sw.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {s['primary']}, stop:1 {s['accent']});"
                             " border-radius: 4px;")
            cell = QHBoxLayout()
            cell.addWidget(sw)
            cell.addWidget(rb)
            style_row.addLayout(cell)
            style_row.addSpacing(10)
            self.style_group.addButton(rb, i)
            if i == 0:
                rb.setChecked(True)
        style_row.addStretch(1)
        lay.addLayout(style_row)
        lay.addStretch(1)
        self.stack.addWidget(page)
        self._template_changed()

    def _selected_categories(self) -> list[str]:
        return [cid for cid, b in self.cat_buttons.items() if b.isChecked()]

    def _categories_changed(self) -> None:
        cats = self._selected_categories()
        suggested = self.templates.suggest_template(cats)
        idx = self.template_combo.findData(suggested)
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)
        no_tpl = [c[language()] if language() in c else c["vi"] for c in CATEGORIES
                  if c["id"] in cats and not c["template"]]
        self.category_note.setText(tr("wiz.category_no_template", cats=", ".join(no_tpl)) if no_tpl else "")

    def _template_changed(self) -> None:
        tid = self.template_combo.currentData()
        if tid:
            t = self.templates.get(tid)
            screens = ", ".join(s["title"] for s in t.screens)
            self.template_desc.setText(f"{t.desc(language())}\n{tr('wiz.screens')}: {screens}")

    # ---- Step 3 ---------------------------------------------------------------
    def _build_step3(self) -> None:
        page, lay = _page(tr("wiz.s3.title"), tr("wiz.s3.sub"))
        form = QFormLayout()
        self.storage = QComboBox()
        self.storage.addItem(tr("wiz.storage_local"), "local")
        self.backend = QComboBox()
        self.backend.addItem(tr("wiz.backend_none"), "none")
        for key, text in (("supabase", "Supabase"), ("firebase", "Firebase"), ("rest", "REST (FastAPI)")):
            self.backend.addItem(f"{text} — {tr('common.planned', milestone='M8')}", key)
            item = self.backend.model().item(self.backend.count() - 1)
            item.setEnabled(False)
        form.addRow(tr("wiz.storage"), self.storage)
        form.addRow(tr("wiz.backend"), self.backend)
        lay.addLayout(form)
        lay.addWidget(label(tr("wiz.capabilities"), "H3"))
        self.caps: dict[str, QCheckBox] = {}
        for key in ("offline", "login", "notifications", "camera", "location"):
            cb = QCheckBox(tr(f"wiz.cap.{key}"))
            cb.setChecked(key == "offline")
            if key in ("notifications", "camera", "location", "login"):
                cb.setToolTip(tr("wiz.cap_sensitive"))
            self.caps[key] = cb
            lay.addWidget(cb)
        lay.addWidget(label(tr("wiz.cap_note"), "Muted", wrap=True))
        lay.addStretch(1)
        self.stack.addWidget(page)

    # ---- Step 4 ---------------------------------------------------------------
    def _build_step4(self) -> None:
        page, lay = _page(tr("wiz.s4.title"), tr("wiz.s4.sub"))
        form = QFormLayout()
        prow = QHBoxLayout()
        self.provider = QComboBox()
        self.provider.addItem(tr("wiz.provider_none"), "")
        for pid, name in PROVIDERS:
            self.provider.addItem(name, pid)
        prow.addWidget(self.provider, 1)
        prow.addWidget(badge(tr("wiz.provider_status"), "warn"))
        self.model = QLineEdit()
        self.model.setPlaceholderText(tr("wiz.model_ph"))
        form.addRow(tr("wiz.provider"), prow)
        form.addRow(tr("wiz.model"), self.model)
        lay.addLayout(form)
        lay.addWidget(label(tr("wiz.mode"), "H3"))
        self.mode_group = QButtonGroup(self)
        for i, m in enumerate(("economy", "balanced", "advanced")):
            rb = QRadioButton(tr(f"wiz.mode.{m}"))
            rb.setProperty("mode", m)
            self.mode_group.addButton(rb, i)
            lay.addWidget(rb)
            if i == 0:
                rb.setChecked(True)
        bform = QFormLayout()
        self.budget_project = QDoubleSpinBox()
        self.budget_project.setRange(0, 1000)
        self.budget_project.setPrefix("$ ")
        self.budget_project.setValue(5)
        self.budget_session = QDoubleSpinBox()
        self.budget_session.setRange(0, 1000)
        self.budget_session.setPrefix("$ ")
        self.budget_session.setValue(1)
        bform.addRow(tr("wiz.budget_project"), self.budget_project)
        bform.addRow(tr("wiz.budget_session"), self.budget_session)
        lay.addLayout(bform)
        lay.addWidget(MilestoneNotice(tr("wiz.ai_notice_title"), "M2", tr("wiz.ai_notice")))
        lay.addStretch(1)
        self.stack.addWidget(page)

    # ---- Step 5 ---------------------------------------------------------------
    def _build_step5(self) -> None:
        page, lay = _page(tr("wiz.s5.title"), tr("wiz.s5.sub"))
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(tr("wiz.prompt_ph"))
        self.prompt.setMinimumHeight(130)
        lay.addWidget(self.prompt)
        row = QHBoxLayout()
        row.addWidget(label(tr("wiz.refs"), "H3"))
        row.addStretch(1)
        add = QPushButton(tr("wiz.refs_add"))
        add.clicked.connect(self._add_refs)
        rm = QPushButton(tr("wiz.refs_remove"))
        rm.clicked.connect(self._remove_ref)
        row.addWidget(add)
        row.addWidget(rm)
        lay.addLayout(row)
        self.ref_list = QListWidget()
        self.ref_list.setFixedHeight(80)
        lay.addWidget(self.ref_list)
        lay.addWidget(label(tr("wiz.refs_note"), "Muted", wrap=True))
        plan_row = QHBoxLayout()
        self.btn_plan = QPushButton(tr("wiz.generate_plan"))
        self.btn_plan.setEnabled(False)
        self.btn_plan.setToolTip(tr("common.planned", milestone="M2–M3"))
        plan_row.addWidget(self.btn_plan)
        plan_row.addWidget(badge(tr("common.planned", milestone="M2–M3"), "warn"))
        plan_row.addStretch(1)
        lay.addLayout(plan_row)
        lay.addWidget(label(tr("wiz.summary"), "H3"))
        self.summary = label("", "Muted", wrap=True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.summary)
        lay.addStretch(1)
        self.stack.addWidget(page)

    def _add_refs(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, tr("wiz.refs_add"), "", REF_FILTER)
        for f in files:
            p = Path(f)
            if p.stat().st_size > MAX_REF_BYTES:
                QMessageBox.warning(self, tr("wiz.refs"), tr("wiz.refs_too_big", name=p.name))
                continue
            if p not in self.references:
                self.references.append(p)
                self.ref_list.addItem(QListWidgetItem(f"{p.name}  ({p.stat().st_size // 1024} KB)"))

    def _remove_ref(self) -> None:
        row = self.ref_list.currentRow()
        if row >= 0:
            self.ref_list.takeItem(row)
            self.references.pop(row)

    # ---- Navigation -------------------------------------------------------------
    def _validate_step(self, idx: int) -> str | None:
        if idx == 0:
            if not self.name.text().strip():
                return tr("wiz.err_name")
            if not is_valid_android_package(self.pkg.text()):
                return tr("wiz.err_pkg")
            if not is_valid_ios_bundle_id(self.bid.text()):
                return tr("wiz.err_bid")
            if not (self.cb_android.isChecked() or self.cb_ios.isChecked()):
                return tr("wiz.err_platform")
            d = self._dest()
            if d.exists() and any(d.iterdir()):
                return tr("wiz.dest_exists")
            if not self.parent_dir.text().strip():
                return tr("wiz.err_parent")
        return None

    def _go(self, idx: int) -> None:
        idx = max(0, min(idx, self.stack.count() - 1))
        cur = self.stack.currentIndex()
        if idx > cur:
            for i in range(cur, idx):
                err = self._validate_step(i)
                if err:
                    self.error_label.setText(err)
                    self.steps.blockSignals(True)
                    self.steps.setCurrentRow(i)
                    self.steps.blockSignals(False)
                    self.stack.setCurrentIndex(i)
                    return
        self.error_label.setText("")
        self.stack.setCurrentIndex(idx)
        self.steps.blockSignals(True)
        self.steps.setCurrentRow(idx)
        self.steps.blockSignals(False)
        last = idx == self.stack.count() - 1
        self.btn_back.setEnabled(idx > 0)
        self.btn_next.setText(tr("wiz.create") if last else tr("wiz.next"))
        if last:
            self._update_summary()

    def _next(self) -> None:
        idx = self.stack.currentIndex()
        if idx < self.stack.count() - 1:
            self._go(idx + 1)
        else:
            self._create()

    def build_spec(self) -> ProjectSpec:
        platforms = [p for p, cb in (("android", self.cb_android), ("ios", self.cb_ios)) if cb.isChecked()]
        style_btn = self.style_group.checkedButton()
        mode_btn = self.mode_group.checkedButton()
        features = [ln.strip() for ln in self.features.toPlainText().splitlines() if ln.strip()]
        return ProjectSpec(
            name=self.name.text().strip(),
            slug=slugify(self.name.text()),
            description=self.desc.toPlainText().strip(),
            language=self.lang.currentData(),
            platforms=platforms,
            android_package=self.pkg.text().strip(),
            ios_bundle_id=self.bid.text().strip(),
            categories=self._selected_categories() or ["custom"],
            template=self.template_combo.currentData(),
            features=features,
            storage=self.storage.currentData(),
            backend=self.backend.currentData(),
            capabilities=CapabilitySpec(**{k: cb.isChecked() for k, cb in self.caps.items()}),
            ai=AIPreferences(
                provider=self.provider.currentData() or "", model=self.model.text().strip(),
                mode=mode_btn.property("mode") if mode_btn else "economy",
                budget_usd_project=self.budget_project.value() or None,
                budget_usd_session=self.budget_session.value() or None,
            ),
            main_prompt=self.prompt.toPlainText().strip(),
            theme=ThemeSpec(style=style_btn.property("style_id") if style_btn else "modern"),
        )

    def _update_summary(self) -> None:
        try:
            spec = self.build_spec()
        except Exception as exc:
            self.summary.setText(str(exc))
            return
        t = self.templates.get(spec.template)
        caps = [k for k, v in spec.capabilities.model_dump().items() if v]
        self.summary.setText(tr(
            "wiz.summary_text", name=spec.name, path=str(self._dest()), template=t.label(language()),
            platforms=", ".join(spec.platforms), style=spec.theme.style, caps=", ".join(caps) or "—",
            refs=len(self.references), sdk=self.templates.sdk().get("expo_sdk", "?"),
        ))

    def _create(self) -> None:
        for i in range(self.stack.count()):
            err = self._validate_step(i)
            if err:
                self._go(i)
                self.error_label.setText(err)
                return
        try:
            spec = self.build_spec()
        except Exception as exc:
            self.error_label.setText(str(exc))
            return
        parent = self.parent_dir.text().strip()
        refs = list(self.references)
        self.btn_next.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.error_label.setText(tr("wiz.creating"))

        def work():
            return self.projects.create_project(spec, parent, refs)

        def done(rec):
            self.created_id = rec.id
            self.accept()

        def failed(msg: str):
            self.btn_next.setEnabled(True)
            self.btn_back.setEnabled(True)
            self.error_label.setText(msg.split("\n\n")[0])

        run_in_background(work, done, failed)
