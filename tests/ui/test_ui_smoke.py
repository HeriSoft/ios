"""UI smoke (offscreen): tạo project tiếng Việt qua wizard, mở workspace, editor lưu + phát hiện xung đột, process runner."""
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.ui


@pytest.fixture
def window(qapp, db):
    from app_builder.core.config import AppSettings
    from app_builder.services.project_service import ProjectService
    from app_builder.ui.main_window import MainWindow
    w = MainWindow(AppSettings(), db, ProjectService(db))
    w.show()
    yield w
    w.runner.stop()
    for ed in w.editors.editors():
        ed.document().setModified(False)
    w.close()


def _wait(qapp, cond, timeout=60.0):
    end = time.time() + timeout
    while time.time() < end:
        qapp.processEvents()
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_wizard_create_and_open(qapp, window, vn_tmp):
    from app_builder.ui.project_wizard import ProjectWizard
    wiz = ProjectWizard(window.projects, str(vn_tmp), window)
    wiz.name.setText("Sổ Thu Chi")
    assert wiz.pkg.text() == "com.example.sothuchi"
    wiz._go(4)  # chưa hợp lệ? -> hợp lệ nên tới bước 5
    assert wiz.stack.currentIndex() == 4
    wiz.cat_buttons["finance"].setChecked(True)
    assert wiz.template_combo.currentData() == "blank"
    assert "Tài chính" in wiz.category_note.text()
    wiz.cat_buttons["productivity"].setChecked(True)
    assert wiz.template_combo.currentData() == "todo"
    assert not wiz.btn_plan.isEnabled()  # chưa có AI -> không đặt nút giả
    wiz._create()
    assert _wait(qapp, lambda: wiz.created_id is not None)
    window.open_project(wiz.created_id)
    assert window.stack.currentIndex() == 1
    assert window.project_panel.screens.count() >= 3
    assert "Sổ Thu Chi" in window.assistant.plan.toPlainText()


def test_wizard_validation(qapp, window, vn_tmp):
    from app_builder.ui.project_wizard import ProjectWizard
    wiz = ProjectWizard(window.projects, str(vn_tmp), window)
    wiz._go(2)
    assert wiz.stack.currentIndex() == 0 and wiz.error_label.text()
    wiz.name.setText("Ok")
    wiz.pkg.setText("invalid")
    wiz._go(1)
    assert wiz.stack.currentIndex() == 0


def test_editor_save_and_conflict(qapp, window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    f = tmp_path / "a.ts"
    f.write_text("const a = 1;\n", "utf-8")
    window.editors.open_file(f)
    ed = window.editors.current_editor()
    ed.selectAll()
    ed.insertPlainText("const a = 2;\n")  # mô phỏng người dùng gõ
    assert ed.dirty
    assert window.editors.save_current()
    assert f.read_text("utf-8") == "const a = 2;\n" and not ed.dirty
    # sửa ngoài IDE, rồi sửa trong IDE -> lưu phải hỏi, chọn Cancel thì không ghi đè
    f.write_text("// external\n", "utf-8")
    ed.selectAll()
    ed.insertPlainText("const a = 3;\n")
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.StandardButton.Cancel)
    assert not window.editors.save_current()
    assert f.read_text("utf-8") == "// external\n"


def test_process_runner_node_version(qapp, db, tmp_path):
    from app_builder.core import process_manager as pm
    from app_builder.ui.process_runner import ProcessRunner
    if not pm.which("node"):
        pytest.skip("Không có Node")
    r = ProcessRunner(db)
    out: list[str] = []
    done: list[int] = []
    r.output.connect(out.append)
    r.finished.connect(lambda j, c: done.append(c))
    jid = r.start(["npm", "--version"], tmp_path, "test")
    assert jid
    assert _wait(qapp, lambda: bool(done), 60)
    assert done[0] == 0
    assert db.query_one("SELECT status FROM jobs WHERE id=?", (jid,))["status"] == "succeeded"


def test_process_runner_stop(qapp, db, tmp_path):
    import sys
    from app_builder.ui.process_runner import ProcessRunner
    r = ProcessRunner(db)
    done: list[int] = []
    r.finished.connect(lambda j, c: done.append(c))
    jid = r.start([sys.executable, "-c", "import time; time.sleep(60)"], tmp_path, "test")
    assert _wait(qapp, lambda: r.running, 10)
    r.stop()
    assert _wait(qapp, lambda: bool(done), 20)
    assert db.query_one("SELECT status FROM jobs WHERE id=?", (jid,))["status"] == "cancelled"


def test_theme_toggle_and_doctor_dialog(qapp, window, monkeypatch):
    window._toggle_theme()
    assert qapp.property("ab_palette") == "light"
    window._toggle_theme()
    from app_builder.ui.doctor_dialog import DoctorDialog
    dlg = DoctorDialog({}, str(Path.home()), window)
    assert _wait(qapp, lambda: dlg.table.rowCount() > 5, 120)
