"""Panel PROJECT bên trái: Files, Screens, Assets, Data/APIs, Dependencies — dữ liệu đọc thật từ workspace."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import (
    QFileDialog, QFileSystemModel, QHBoxLayout, QInputDialog, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QPlainTextEdit, QPushButton, QToolBox, QTreeView, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QFile

from app_builder.core.i18n import tr
from app_builder.core.workspace import IGNORED_DIRS, UnsafePathError, atomic_write_text, resolve_inside
from app_builder.services import project_inspect as pi
from app_builder.services.project_service import ProjectService
from app_builder.ui.widgets import label, run_in_background

ASSET_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".ttf", ".otf", ".webp"}
MAX_ASSET_BYTES = 10 * 1024 * 1024


class _HideIgnored(QSortFilterProxyModel):
    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:  # noqa: N802
        model: QFileSystemModel = self.sourceModel()
        idx = model.index(row, 0, parent)
        name = model.fileName(idx)
        if model.isDir(idx) and (name in IGNORED_DIRS or name.startswith(".tmp-")):
            return False
        return not name.startswith(".tmp-")


class ProjectPanel(QWidget):
    open_file = Signal(Path)
    request_install = Signal()
    status = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.root: Path | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(label(tr("panel.project").upper(), "SectionTitle"))
        self.box = QToolBox()
        lay.addWidget(self.box, 1)

        # Files
        files = QWidget()
        fl = QVBoxLayout(files)
        fl.setContentsMargins(4, 2, 4, 4)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("panel.search"))
        self.search.setClearButtonEnabled(True)
        self.search.returnPressed.connect(self._search)
        self.search.textChanged.connect(lambda t: self.results.setVisible(bool(t)) if not t else None)
        fl.addWidget(self.search)
        self.results = QListWidget()
        self.results.setVisible(False)
        self.results.itemActivated.connect(self._open_result)
        fl.addWidget(self.results, 1)
        self.fs = QFileSystemModel(self)
        self.fs.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)
        self.proxy = _HideIgnored(self)
        self.proxy.setSourceModel(self.fs)
        self.tree = QTreeView()
        self.tree.setModel(self.proxy)
        self.tree.setHeaderHidden(True)
        for c in (1, 2, 3):
            self.tree.hideColumn(c)
        self.tree.doubleClicked.connect(self._activated)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_menu)
        fl.addWidget(self.tree, 3)
        self.box.addItem(files, tr("panel.files"))

        # Screens
        self.screens = QListWidget()
        self.screens.itemActivated.connect(lambda it: self._open_rel(it.data(Qt.ItemDataRole.UserRole)))
        self.box.addItem(self.screens, tr("panel.screens"))

        # Assets
        assets = QWidget()
        al = QVBoxLayout(assets)
        al.setContentsMargins(4, 2, 4, 4)
        self.assets = QListWidget()
        al.addWidget(self.assets, 1)
        imp = QPushButton(tr("panel.asset_import"))
        imp.clicked.connect(self._import_asset)
        al.addWidget(imp)
        self.box.addItem(assets, tr("panel.assets"))

        # Data / APIs
        self.data_view = QPlainTextEdit()
        self.data_view.setReadOnly(True)
        self.box.addItem(self.data_view, tr("panel.data"))

        # Dependencies
        deps = QWidget()
        dl = QVBoxLayout(deps)
        dl.setContentsMargins(4, 2, 4, 4)
        self.deps_status = label("", "Muted", wrap=True)
        dl.addWidget(self.deps_status)
        self.deps = QListWidget()
        dl.addWidget(self.deps, 1)
        row = QHBoxLayout()
        self.btn_install = QPushButton(tr("panel.install"))
        self.btn_install.clicked.connect(self.request_install.emit)
        refresh = QPushButton("⟳")
        refresh.setToolTip(tr("common.refresh"))
        refresh.clicked.connect(self.refresh)
        row.addWidget(self.btn_install, 1)
        row.addWidget(refresh)
        dl.addLayout(row)
        self.box.addItem(deps, tr("panel.deps"))

    # ------------------------------------------------------------------
    def set_project(self, root: Path | None) -> None:
        self.root = root
        self.results.clear()
        self.results.setVisible(False)
        if root is None:
            self.tree.setRootIndex(QModelIndex())
            return
        src_idx = self.fs.setRootPath(str(root))
        self.tree.setRootIndex(self.proxy.mapFromSource(src_idx))
        self.refresh()

    def refresh(self) -> None:
        if not self.root:
            return
        root = self.root
        # Screens
        self.screens.clear()
        for r in pi.routes_from_app_dir(root):
            icon = {"screen": "▣", "layout": "▤", "special": "◇"}[r.kind]
            it = QListWidgetItem(f"{icon}  {r.route}   ·  {r.file.removeprefix('app/')}")
            it.setData(Qt.ItemDataRole.UserRole, r.file)
            it.setToolTip(r.file)
            self.screens.addItem(it)
        if self.screens.count() == 0:
            self.screens.addItem(tr("panel.no_routes"))
        # Assets
        self.assets.clear()
        adir = root / "assets"
        meta = self._asset_meta()
        if adir.is_dir():
            for f in sorted(adir.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(root).as_posix()
                    info = f"{f.stat().st_size // 1024} KB"
                    if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                        size = QImageReader(str(f)).size()
                        if size.isValid():
                            info += f", {size.width()}×{size.height()}"
                    lic = meta.get(rel, {}).get("license")
                    it = QListWidgetItem(f"{rel}  ({info})" + (f" — {lic}" if lic else ""))
                    it.setData(Qt.ItemDataRole.UserRole, rel)
                    self.assets.addItem(it)
        if self.assets.count() == 0:
            self.assets.addItem(tr("panel.no_assets"))
        # Data
        spec = ProjectService.load_spec(root)
        if spec:
            caps = ", ".join(k for k, v in spec.capabilities.model_dump().items() if v) or "—"
            text = [f"{tr('panel.storage')}: {spec.storage}", f"Backend: {spec.backend}", f"{tr('panel.capabilities')}: {caps}", ""]
            for ent in spec.data_model:
                text.append(json.dumps(ent, ensure_ascii=False, indent=2))
            self.data_view.setPlainText("\n".join(text))
        else:
            self.data_view.setPlainText(tr("panel.no_spec"))
        # Deps
        d = pi.read_dependencies(root)
        self.deps.clear()
        for section in ("dependencies", "devDependencies"):
            for name, ver in d[section].items():
                inst = pi.installed_version(root, name) if d["installed"] else None
                mark = f" → {inst}" if inst else ""
                self.deps.addItem(f"{'⚙ ' if section == 'devDependencies' else ''}{name}  {ver}{mark}")
        if d["error"]:
            self.deps_status.setText(d["error"])
        else:
            self.deps_status.setText(tr("panel.deps_installed") if d["installed"] else tr("panel.deps_not_installed"))

    # ---- files ------------------------------------------------------------
    def _path_of(self, proxy_idx: QModelIndex) -> Path:
        return Path(self.fs.filePath(self.proxy.mapToSource(proxy_idx)))

    def _activated(self, idx: QModelIndex) -> None:
        p = self._path_of(idx)
        if p.is_file():
            self.open_file.emit(p)

    def _open_rel(self, rel: str | None) -> None:
        if rel and self.root:
            self.open_file.emit(self.root / rel)

    def _search(self) -> None:
        q = self.search.text().strip()
        if not q or not self.root:
            return
        self.results.clear()
        self.results.setVisible(True)
        self.results.addItem(tr("panel.searching"))
        root = self.root

        def done(items):
            self.results.clear()
            for rel, line, preview in items:
                text = rel if not line else f"{rel}:{line}  {preview}"
                it = QListWidgetItem(text)
                it.setData(Qt.ItemDataRole.UserRole, rel)
                self.results.addItem(it)
            if not items:
                self.results.addItem(tr("panel.no_results"))

        run_in_background(lambda: pi.search_project(root, q), done, lambda m: self.status.emit(m))

    def _open_result(self, item: QListWidgetItem) -> None:
        self._open_rel(item.data(Qt.ItemDataRole.UserRole))

    def _tree_menu(self, pos) -> None:
        if not self.root:
            return
        idx = self.tree.indexAt(pos)
        target = self._path_of(idx) if idx.isValid() else self.root
        base = target if target.is_dir() else target.parent
        m = QMenu(self)
        a_file = m.addAction(tr("panel.new_file"))
        a_dir = m.addAction(tr("panel.new_folder"))
        a_ren = m.addAction(tr("panel.rename"))
        a_del = m.addAction(tr("panel.delete"))
        if not idx.isValid():
            a_ren.setEnabled(False)
            a_del.setEnabled(False)
        chosen = m.exec(self.tree.viewport().mapToGlobal(pos))
        try:
            if chosen is a_file or chosen is a_dir:
                name, ok = QInputDialog.getText(self, chosen.text(), tr("panel.name"))
                if not ok or not name.strip():
                    return
                rel = (base / name.strip()).relative_to(self.root).as_posix()
                p = resolve_inside(self.root, rel)
                if p.exists():
                    raise UnsafePathError(tr("panel.exists"))
                if chosen is a_dir:
                    p.mkdir(parents=True)
                else:
                    atomic_write_text(p, "")
                    self.open_file.emit(p)
            elif chosen is a_ren:
                name, ok = QInputDialog.getText(self, tr("panel.rename"), tr("panel.name"), text=target.name)
                if ok and name.strip() and name.strip() != target.name:
                    rel = (target.parent / name.strip()).relative_to(self.root).as_posix()
                    p = resolve_inside(self.root, rel)
                    if p.exists():
                        raise UnsafePathError(tr("panel.exists"))
                    target.rename(p)
            elif chosen is a_del:
                if QMessageBox.question(self, tr("panel.delete"), tr("panel.delete_confirm", name=target.name)) \
                        == QMessageBox.StandardButton.Yes:
                    # Chuyển vào Thùng rác (có thể khôi phục), không xóa vĩnh viễn
                    if not QFile.moveToTrash(str(target)):
                        QMessageBox.warning(self, tr("panel.delete"), tr("panel.trash_failed"))
        except (UnsafePathError, OSError, ValueError) as exc:
            QMessageBox.warning(self, tr("panel.files"), str(exc))
        self.refresh()

    # ---- assets -----------------------------------------------------------
    def _asset_meta_path(self) -> Path:
        return self.root / ".appbuilder" / "assets.json"  # type: ignore[operator]

    def _asset_meta(self) -> dict:
        try:
            return json.loads(self._asset_meta_path().read_text("utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

    def _import_asset(self) -> None:
        if not self.root:
            return
        files, _ = QFileDialog.getOpenFileNames(self, tr("panel.asset_import"), "",
                                                "Assets (*.png *.jpg *.jpeg *.svg *.webp *.ttf *.otf)")
        if not files:
            return
        lic, ok = QInputDialog.getText(self, tr("panel.asset_import"), tr("panel.asset_license"))
        if not ok:
            return
        meta = self._asset_meta()
        for f in files:
            src = Path(f)
            if src.suffix.lower() not in ASSET_EXTS:
                continue
            if src.stat().st_size > MAX_ASSET_BYTES:
                QMessageBox.warning(self, tr("panel.assets"), tr("panel.asset_too_big", name=src.name))
                continue
            sub = "fonts" if src.suffix.lower() in {".ttf", ".otf"} else "images"
            dest = resolve_inside(self.root, f"assets/{sub}/{src.name}")
            if dest.exists() and QMessageBox.question(self, tr("panel.assets"), tr("panel.asset_overwrite", name=src.name)) \
                    != QMessageBox.StandardButton.Yes:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            meta[dest.relative_to(self.root).as_posix()] = {"license": lic.strip(), "source": src.name}
        atomic_write_text(self._asset_meta_path(), json.dumps(meta, indent=2, ensure_ascii=False))
        self.refresh()
