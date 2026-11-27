"""Theme dark/light cho IDE (QSS). Màu nhận diện riêng, không sao chép UI sản phẩm khác."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str          # nền cửa sổ
    panel: str       # nền panel
    panel_alt: str   # nền nổi (card, input)
    border: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    accent_text: str
    danger: str
    warn: str
    ok: str
    selection: str
    editor_bg: str


DARK = Palette("dark", "#0F1218", "#151A22", "#1C222D", "#272F3C", "#E6E9EF", "#8B95A7",
               "#7C6CF2", "#9183F5", "#FFFFFF", "#F2668B", "#F5B94A", "#3DD68C", "#2D3550", "#11151C")
LIGHT = Palette("light", "#F3F4F8", "#FFFFFF", "#F7F8FB", "#DCE0E8", "#1B2030", "#5E6678",
                "#5B4BE0", "#6F60EA", "#FFFFFF", "#D33B62", "#B7791F", "#15935B", "#DCD8FB", "#FFFFFF")


def palette_for(name: str) -> Palette:
    return LIGHT if name == "light" else DARK


def build_qss(p: Palette) -> str:
    return f"""
* {{ font-family: "Segoe UI", "Segoe UI Variable", sans-serif; font-size: 10pt; color: {p.text}; }}
QMainWindow, QDialog, QWidget#Root {{ background: {p.bg}; }}
QWidget#Panel, QFrame#Panel {{ background: {p.panel}; }}
QFrame#Card {{ background: {p.panel}; border: 1px solid {p.border}; border-radius: 12px; }}
QFrame#Card:hover {{ border-color: {p.accent}; }}
QFrame#Notice {{ background: {p.panel_alt}; border: 1px dashed {p.border}; border-radius: 10px; }}
QLabel#H1 {{ font-size: 20pt; font-weight: 700; }}
QLabel#H2 {{ font-size: 13pt; font-weight: 600; }}
QLabel#H3 {{ font-size: 10.5pt; font-weight: 600; }}
QLabel#Muted {{ color: {p.muted}; }}
QLabel#SectionTitle {{ color: {p.muted}; font-size: 8.5pt; font-weight: 700; letter-spacing: 1px; padding: 6px 8px 2px 8px; }}
QLabel#Badge {{ background: {p.panel_alt}; border: 1px solid {p.border}; border-radius: 9px; padding: 1px 8px; color: {p.muted}; font-size: 8.5pt; }}
QLabel#BadgeOk {{ background: transparent; border: 1px solid {p.ok}; border-radius: 9px; padding: 1px 8px; color: {p.ok}; font-size: 8.5pt; }}
QLabel#BadgeWarn {{ background: transparent; border: 1px solid {p.warn}; border-radius: 9px; padding: 1px 8px; color: {p.warn}; font-size: 8.5pt; }}
QLabel#BadgeDanger {{ background: transparent; border: 1px solid {p.danger}; border-radius: 9px; padding: 1px 8px; color: {p.danger}; font-size: 8.5pt; }}
QLabel#Logo {{ font-size: 11pt; font-weight: 800; color: {p.accent}; padding: 0 6px; }}

QPushButton {{ background: {p.panel_alt}; border: 1px solid {p.border}; border-radius: 8px; padding: 6px 14px; }}
QPushButton:hover {{ border-color: {p.accent}; }}
QPushButton:pressed {{ background: {p.selection}; }}
QPushButton:disabled {{ color: {p.muted}; border-color: {p.border}; background: {p.panel}; }}
QPushButton#Primary {{ background: {p.accent}; border: 1px solid {p.accent}; color: {p.accent_text}; font-weight: 600; }}
QPushButton#Primary:hover {{ background: {p.accent_hover}; }}
QPushButton#Primary:disabled {{ background: {p.panel_alt}; color: {p.muted}; border-color: {p.border}; }}
QPushButton#Danger {{ color: {p.danger}; }}
QPushButton#Flat {{ background: transparent; border: none; padding: 4px 8px; }}
QPushButton#Flat:hover {{ background: {p.panel_alt}; }}
QPushButton#CategoryChip {{ border-radius: 14px; padding: 6px 12px; text-align: left; }}
QPushButton#CategoryChip:checked {{ background: {p.selection}; border-color: {p.accent}; color: {p.text}; }}

QToolBar {{ background: {p.panel}; border: none; border-bottom: 1px solid {p.border}; spacing: 4px; padding: 4px 6px; }}
QToolBar QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 4px 8px; }}
QToolBar QToolButton:hover {{ background: {p.panel_alt}; border-color: {p.border}; }}
QToolBar QToolButton:disabled {{ color: {p.muted}; }}
QToolBar::separator {{ background: {p.border}; width: 1px; margin: 4px 6px; }}

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
  background: {p.panel_alt}; border: 1px solid {p.border}; border-radius: 8px; padding: 5px 8px;
  selection-background-color: {p.selection}; selection-color: {p.text};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {p.accent}; }}
QLineEdit[invalid="true"] {{ border-color: {p.danger}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {p.panel}; border: 1px solid {p.border}; selection-background-color: {p.selection}; }}
QPlainTextEdit#Editor {{ background: {p.editor_bg}; border: none; border-radius: 0; font-family: "Cascadia Code", "Consolas", monospace; font-size: 10.5pt; }}
QPlainTextEdit#Console {{ background: {p.editor_bg}; border: none; border-radius: 0; font-family: "Cascadia Mono", "Consolas", monospace; font-size: 9.5pt; }}

QTabWidget::pane {{ border: none; background: {p.panel}; }}
QTabBar::tab {{ background: transparent; padding: 7px 14px; border: none; border-bottom: 2px solid transparent; color: {p.muted}; }}
QTabBar::tab:selected {{ color: {p.text}; border-bottom-color: {p.accent}; }}
QTabBar::tab:hover {{ color: {p.text}; }}
QTabBar::close-button {{ subcontrol-position: right; }}

QTreeView, QListWidget, QListView, QTableWidget {{ background: {p.panel}; border: none; outline: 0; }}
QTreeView::item, QListWidget::item {{ padding: 3px 4px; border-radius: 4px; }}
QTreeView::item:hover, QListWidget::item:hover {{ background: {p.panel_alt}; }}
QTreeView::item:selected, QListWidget::item:selected, QTableWidget::item:selected {{ background: {p.selection}; color: {p.text}; }}
QHeaderView::section {{ background: {p.panel}; color: {p.muted}; border: none; border-bottom: 1px solid {p.border}; padding: 4px 6px; }}

QSplitter::handle {{ background: {p.border}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 5px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {p.border}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollArea {{ border: none; background: transparent; }}
QStatusBar {{ background: {p.panel}; border-top: 1px solid {p.border}; color: {p.muted}; }}
QCheckBox, QRadioButton {{ spacing: 8px; }}
QGroupBox {{ border: 1px solid {p.border}; border-radius: 10px; margin-top: 14px; padding: 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {p.muted}; }}
QMenu {{ background: {p.panel}; border: 1px solid {p.border}; padding: 4px; }}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
QMenu::item:selected {{ background: {p.selection}; }}
QMenu::item:disabled {{ color: {p.muted}; }}
QToolTip {{ background: {p.panel_alt}; color: {p.text}; border: 1px solid {p.border}; padding: 4px; }}
QToolBox {{ background: {p.panel}; }}
QToolBox::tab {{ background: {p.panel}; border: none; border-top: 1px solid {p.border}; padding: 6px 10px;
  color: {p.muted}; font-weight: 600; }}
QToolBox::tab:selected {{ color: {p.text}; background: {p.panel_alt}; }}
QToolBox::tab:hover {{ color: {p.text}; }}
QListWidget#StepList {{ background: transparent; }}
QListWidget#StepList::item {{ padding: 10px 12px; margin: 2px 0; border-radius: 8px; color: {p.muted}; }}
QListWidget#StepList::item:selected {{ background: {p.selection}; color: {p.text}; font-weight: 600; }}
"""


def apply_theme(app: QApplication, name: str) -> Palette:
    p = palette_for(name)
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(p.bg))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(p.text))
    pal.setColor(QPalette.ColorRole.Base, QColor(p.panel_alt))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(p.panel))
    pal.setColor(QPalette.ColorRole.Text, QColor(p.text))
    pal.setColor(QPalette.ColorRole.Button, QColor(p.panel_alt))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(p.text))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(p.selection))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(p.text))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(p.muted))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(p.panel_alt))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(p.text))
    app.setPalette(pal)
    app.setStyleSheet(build_qss(p))
    app.setProperty("ab_palette", p.name)
    return p


def current_palette() -> Palette:
    app = QApplication.instance()
    return palette_for(app.property("ab_palette") if app else "dark")
