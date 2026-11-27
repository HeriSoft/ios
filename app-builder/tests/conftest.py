import os
import sys
import tempfile
from pathlib import Path

import pytest

# Cô lập dữ liệu test khỏi %LOCALAPPDATA% thật
_TMP = Path(tempfile.mkdtemp(prefix="abai-test-"))
os.environ["APPBUILDER_DATA_DIR"] = str(_TMP / "data")
os.environ["APPBUILDER_WORKSPACE_DIR"] = str(_TMP / "workspace")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def vn_tmp(tmp_path: Path) -> Path:
    """Thư mục tạm có dấu tiếng Việt và khoảng trắng."""
    p = tmp_path / "Thư mục có dấu" / "Dự án"
    p.mkdir(parents=True)
    return p


@pytest.fixture
def db():
    from app_builder.core.database import Database
    d = Database(":memory:")
    yield d
    d.close()


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from app_builder.ui.theme import apply_theme
    apply_theme(app, "dark")
    return app
