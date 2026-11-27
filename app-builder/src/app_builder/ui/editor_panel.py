"""Code editor MVP: QPlainTextEdit + số dòng + syntax highlight (TS/JSON/CSS/Python),
tabs, dirty state, lưu nguyên tử, phát hiện file thay đổi ngoài IDE bằng SHA256 (không overwrite âm thầm)."""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QRect, QRegularExpression, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QShortcut, QSyntaxHighlighter, QTextCharFormat, QTextFormat
from PySide6.QtWidgets import QMessageBox, QPlainTextEdit, QTabWidget, QTextEdit, QWidget

from app_builder.core.i18n import tr
from app_builder.core.workspace import atomic_write_bytes, sha256_bytes, sha256_file
from app_builder.ui.theme import current_palette

MAX_OPEN_BYTES = 2 * 1024 * 1024


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    f.setFontItalic(italic)
    return f


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, lang: str) -> None:
        super().__init__(doc)
        dark = current_palette().name == "dark"
        c = {
            "kw": "#C792EA" if dark else "#7C3AED", "str": "#A5E075" if dark else "#15803D",
            "num": "#F78C6C" if dark else "#C2410C", "com": "#6B7689" if dark else "#8A94A6",
            "type": "#82AAFF" if dark else "#1D4ED8", "tag": "#FF7AA2" if dark else "#BE185D",
            "key": "#7FDBCA" if dark else "#0E7490",
        }
        self.rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self.ml_comment = lang in ("ts", "css")
        if lang == "ts":
            kws = ("import export from default const let var function return if else for while do switch case break "
                   "continue new class extends implements interface type enum as async await try catch finally throw "
                   "typeof instanceof in of null undefined true false this void keyof readonly public private protected")
            self._add(r"\b(" + "|".join(kws.split()) + r")\b", _fmt(c["kw"], bold=True))
            self._add(r"\b[A-Z][A-Za-z0-9_]*\b", _fmt(c["type"]))
            self._add(r"</?[A-Za-z][A-Za-z0-9.]*", _fmt(c["tag"]))
            self._add(r"\b\d+(\.\d+)?\b", _fmt(c["num"]))
            self._add(r"\"[^\"\\]*(\\.[^\"\\]*)*\"|'[^'\\]*(\\.[^'\\]*)*'|`[^`]*`", _fmt(c["str"]))
            self._add(r"//[^\n]*", _fmt(c["com"], italic=True))
        elif lang == "json":
            self._add(r"\"[^\"\\]*(\\.[^\"\\]*)*\"\s*(?=:)", _fmt(c["key"]))
            self._add(r":\s*\"[^\"\\]*(\\.[^\"\\]*)*\"", _fmt(c["str"]))
            self._add(r"\b(true|false|null)\b|\b-?\d+(\.\d+)?\b", _fmt(c["num"]))
        elif lang == "css":
            self._add(r"[.#]?[A-Za-z_-][\w-]*\s*(?=\{)", _fmt(c["type"]))
            self._add(r"[\w-]+\s*(?=:)", _fmt(c["key"]))
            self._add(r"#[0-9a-fA-F]{3,8}\b|\b\d+(px|rem|em|%)?\b", _fmt(c["num"]))
        elif lang == "py":
            kws = ("def class return if elif else for while import from as with try except finally raise pass "
                   "lambda yield async await None True False and or not in is global nonlocal break continue")
            self._add(r"\b(" + "|".join(kws.split()) + r")\b", _fmt(c["kw"], bold=True))
            self._add(r"\b\d+(\.\d+)?\b", _fmt(c["num"]))
            self._add(r"\"[^\"\\]*(\\.[^\"\\]*)*\"|'[^'\\]*(\\.[^'\\]*)*'", _fmt(c["str"]))
            self._add(r"#[^\n]*", _fmt(c["com"], italic=True))
        elif lang == "md":
            self._add(r"^#{1,6}\s.*$", _fmt(c["type"], bold=True))
            self._add(r"`[^`]+`", _fmt(c["str"]))
        self.com_fmt = _fmt(c["com"], italic=True)
        self.start_re = QRegularExpression(r"/\*")
        self.end_re = QRegularExpression(r"\*/")

    def _add(self, pattern: str, fmt: QTextCharFormat) -> None:
        self.rules.append((QRegularExpression(pattern), fmt))

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        for rx, fmt in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
        if not self.ml_comment:
            return
        self.setCurrentBlockState(0)
        continuing = self.previousBlockState() == 1
        start = 0 if continuing else text.find("/*")
        while start >= 0:
            end = text.find("*/", start if continuing else start + 2)
            continuing = False
            if end < 0:
                self.setCurrentBlockState(1)
                self.setFormat(start, len(text) - start, self.com_fmt)
                break
            self.setFormat(start, end - start + 2, self.com_fmt)
            start = text.find("/*", end + 2)


def lang_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {".ts": "ts", ".tsx": "ts", ".js": "ts", ".jsx": "ts", ".mjs": "ts", ".json": "json",
            ".css": "css", ".py": "py", ".md": "md"}.get(ext, "")


class _LineArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self.editor.line_area_width(), 0)

    def paintEvent(self, e) -> None:  # noqa: N802
        self.editor.paint_line_numbers(e)


class CodeEditor(QPlainTextEdit):
    dirty_changed = Signal(bool)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.setObjectName("Editor")
        self.path = path
        self.disk_hash: str | None = None
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 2)
        self.line_area = _LineArea(self)
        self.blockCountChanged.connect(lambda _: self.setViewportMargins(self.line_area_width(), 0, 0, 0))
        self.updateRequest.connect(self._update_area)
        self.cursorPositionChanged.connect(self._highlight_line)
        self.setViewportMargins(self.line_area_width(), 0, 0, 0)
        self.highlighter = CodeHighlighter(self.document(), lang_for(path))
        self.document().modificationChanged.connect(self.dirty_changed.emit)

    def load(self) -> None:
        data = self.path.read_bytes()
        self.disk_hash = sha256_bytes(data)
        self.setPlainText(data.decode("utf-8", errors="replace"))
        self.document().setModified(False)

    @property
    def dirty(self) -> bool:
        return self.document().isModified()

    def save(self) -> None:
        data = self.toPlainText().encode("utf-8")
        atomic_write_bytes(self.path, data)
        self.disk_hash = sha256_bytes(data)
        self.document().setModified(False)

    # line numbers
    def line_area_width(self) -> int:
        digits = max(3, len(str(self.blockCount())))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())

    def resizeEvent(self, e) -> None:  # noqa: N802
        super().resizeEvent(e)
        cr = self.contentsRect()
        self.line_area.setGeometry(QRect(cr.left(), cr.top(), self.line_area_width(), cr.height()))

    def paint_line_numbers(self, event) -> None:
        p = current_palette()
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), QColor(p.editor_bg))
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(p.text if num == current else p.muted))
                painter.drawText(0, top, self.line_area.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num += 1

    def _highlight_line(self) -> None:
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(current_palette().panel_alt))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])

    def keyPressEvent(self, e) -> None:  # noqa: N802
        # Giữ thụt lề khi xuống dòng
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not e.modifiers():
            line = self.textCursor().block().text()
            indent = re.match(r"[ \t]*", line).group(0)
            if line.rstrip().endswith(("{", "(", "[", ":")):
                indent += "  "
            super().keyPressEvent(e)
            self.insertPlainText(indent)
            return
        if e.key() == Qt.Key.Key_Tab and not e.modifiers():
            self.insertPlainText("  ")
            return
        super().keyPressEvent(e)


class EditorTabs(QTabWidget):
    """Quản lý các file đang mở trong project."""
    status = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._on_external_change)
        self._pending: set[str] = set()
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(400)
        self._debounce.timeout.connect(self._process_external)
        QShortcut(QKeySequence.StandardKey.Save, self, activated=self.save_current)

    def editors(self) -> list[CodeEditor]:
        return [self.widget(i) for i in range(self.count()) if isinstance(self.widget(i), CodeEditor)]

    def current_editor(self) -> CodeEditor | None:
        w = self.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def open_file(self, path: Path) -> None:
        path = Path(path)
        for i, ed in enumerate(self.editors()):
            if ed.path == path:
                self.setCurrentIndex(self.indexOf(ed))
                return
        if not path.is_file():
            return
        if path.stat().st_size > MAX_OPEN_BYTES:
            QMessageBox.information(self, tr("editor.title"), tr("editor.too_big"))
            return
        raw = path.read_bytes()[:4096]
        if b"\x00" in raw:
            QMessageBox.information(self, tr("editor.title"), tr("editor.binary"))
            return
        ed = CodeEditor(path)
        ed.load()
        ed.dirty_changed.connect(lambda d, e=ed: self._update_title(e))
        idx = self.addTab(ed, path.name)
        self.setTabToolTip(idx, str(path))
        self.setCurrentIndex(idx)
        self.watcher.addPath(str(path))

    def _update_title(self, ed: CodeEditor) -> None:
        idx = self.indexOf(ed)
        if idx >= 0:
            self.setTabText(idx, ("● " if ed.dirty else "") + ed.path.name)

    def save_current(self) -> bool:
        ed = self.current_editor()
        return self.save_editor(ed) if ed else False

    def save_editor(self, ed: CodeEditor) -> bool:
        on_disk = sha256_file(ed.path)
        if on_disk is not None and ed.disk_hash is not None and on_disk != ed.disk_hash:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(tr("editor.conflict_title"))
            box.setText(tr("editor.conflict", name=ed.path.name))
            overwrite = box.addButton(tr("editor.overwrite"), QMessageBox.ButtonRole.DestructiveRole)
            reload_btn = box.addButton(tr("editor.reload"), QMessageBox.ButtonRole.AcceptRole)
            box.addButton(QMessageBox.StandardButton.Cancel)
            box.exec()
            if box.clickedButton() is reload_btn:
                ed.load()
                return False
            if box.clickedButton() is not overwrite:
                return False
        self.watcher.removePath(str(ed.path))
        try:
            ed.save()
        except OSError as exc:
            QMessageBox.critical(self, tr("editor.title"), str(exc))
            return False
        finally:
            self.watcher.addPath(str(ed.path))
        self._update_title(ed)
        self.status.emit(tr("editor.saved", name=ed.path.name))
        return True

    def close_tab(self, idx: int) -> bool:
        ed = self.widget(idx)
        if isinstance(ed, CodeEditor) and ed.dirty:
            r = QMessageBox.question(self, tr("editor.title"), tr("editor.unsaved", name=ed.path.name),
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
                                     | QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Cancel:
                return False
            if r == QMessageBox.StandardButton.Save and not self.save_editor(ed):
                return False
        if isinstance(ed, CodeEditor):
            self.watcher.removePath(str(ed.path))
        self.removeTab(idx)
        if ed:
            ed.deleteLater()
        return True

    def close_all(self) -> bool:
        while self.count():
            if not self.close_tab(0):
                return False
        return True

    def _on_external_change(self, path: str) -> None:
        self._pending.add(path)
        self._debounce.start()

    def _process_external(self) -> None:
        pending, self._pending = self._pending, set()
        for ed in self.editors():
            if str(ed.path) not in pending:
                continue
            if Path(ed.path).exists():
                self.watcher.addPath(str(ed.path))  # một số editor ghi bằng replace -> mất watch
            new_hash = sha256_file(ed.path)
            if new_hash is None or new_hash == ed.disk_hash:
                continue
            if not ed.dirty:
                ed.load()
                self.status.emit(tr("editor.reloaded", name=ed.path.name))
            else:
                self.status.emit(tr("editor.changed_outside", name=ed.path.name))
