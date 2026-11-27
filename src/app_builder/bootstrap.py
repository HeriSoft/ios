"""Khởi tạo: logging (rotate + redact), settings, database, services, Qt application."""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app_builder import APP_ID, APP_NAME, __version__
from app_builder.core.config import data_dir, load_settings, logs_dir
from app_builder.core.database import Database
from app_builder.core.i18n import set_language
from app_builder.core.redaction import RedactingFilter


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if any(getattr(h, "_ab", False) for h in root.handlers):
        return
    root.setLevel(level)
    fh = RotatingFileHandler(logs_dir() / "app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    fh.addFilter(RedactingFilter())
    fh._ab = True  # type: ignore[attr-defined]
    root.addHandler(fh)
    if sys.stderr:
        sh = logging.StreamHandler()
        sh.setLevel(logging.WARNING)
        sh.addFilter(RedactingFilter())
        sh._ab = True  # type: ignore[attr-defined]
        root.addHandler(sh)


def open_database() -> Database:
    return Database(data_dir() / "appbuilder.db")


def run_gui(argv: list[str]) -> int:
    setup_logging()
    log = logging.getLogger("app_builder")
    settings = load_settings()
    set_language(settings.language)

    # Qt WebEngine cần đặt trước khi tạo QApplication
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-logging")
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtGui import QFont, QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401  (khởi tạo sớm nếu có)
    except ImportError:
        log.info("Qt WebEngine không khả dụng; preview sẽ dùng trình duyệt ngoài")

    app = QApplication(argv)
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setFont(QFont("Segoe UI", 10))
    from app_builder.ui.theme import apply_theme
    apply_theme(app, settings.theme)

    try:
        db = open_database()
    except Exception as exc:  # pragma: no cover
        QMessageBox.critical(None, APP_NAME, f"Không mở được cơ sở dữ liệu:\n{exc}")
        return 1

    from app_builder.services.project_service import ProjectService
    from app_builder.ui.main_window import MainWindow

    win = MainWindow(settings, db, ProjectService(db))
    win.show()
    log.info("%s %s started (data: %s)", APP_NAME, __version__, data_dir())
    code = app.exec()
    db.close()
    return code
