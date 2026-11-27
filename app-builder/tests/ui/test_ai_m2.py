"""UI M2 (offscreen, provider TEST, không gọi mạng): chat streaming, Dừng, lỗi, ngân sách, kết nối, chi phí."""
import time

import pytest
from PySide6.QtWidgets import QMessageBox

pytestmark = pytest.mark.ui


def _wait(qapp, cond, timeout=20.0):
    end = time.time() + timeout
    while time.time() < end:
        qapp.processEvents()
        if cond():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def window(qapp, db, monkeypatch):
    monkeypatch.setenv("APPBUILDER_FAKE_PROVIDER", "1")
    from app_builder.core.config import AppSettings
    from app_builder.core.secret_store import SecretStore
    from app_builder.services.project_service import ProjectService
    from app_builder.ui.main_window import MainWindow
    w = MainWindow(AppSettings(), db, ProjectService(db), secrets=SecretStore(use_keyring=False))
    w.show()
    yield w
    if w.assistant.stream:
        w.assistant.stop()
        w.assistant.stream.wait(5000)
    w.close()


def _ask(qapp, panel, text, model="fake-echo"):
    panel.reload_providers()
    panel.provider.setCurrentIndex(panel.provider.findData("fake"))
    idx = panel.model.findData(model)
    if idx >= 0:
        panel.model.setCurrentIndex(idx)
    else:
        panel.model.setEditText(model)
    panel.prompt.setPlainText(text)
    panel.send()


def test_chat_streams_and_records_usage(qapp, window):
    panel = window.assistant
    assert panel.provider.findData("fake") >= 0
    _ask(qapp, panel, "Thêm màn hình đăng nhập")
    assert _wait(qapp, lambda: panel.stream is None)
    assert "[TEST] Bạn vừa hỏi: Thêm màn hình đăng nhập" in panel.transcript.toPlainText()
    assert [m.role for m in panel.history] == ["user", "assistant"]
    row = window.budget.recent()[0]
    assert (row["provider"], row["model"], row["status"]) == ("fake", "fake-echo", "ok")
    assert row["output_tokens"] > 0 and "token" in panel.usage_label.text()
    assert "$" in window.budget_badge.text()
    # Lượt thứ hai gửi kèm lịch sử
    _ask(qapp, panel, "Còn gì nữa?")
    assert _wait(qapp, lambda: panel.stream is None)
    assert len(panel.history) == 4
    panel.new_chat()
    assert panel.history == [] and panel.transcript.toPlainText() == ""


def test_stop_cancels_stream(qapp, window, monkeypatch):
    from app_builder.providers.fake_provider import FakeProvider
    panel = window.assistant
    monkeypatch.setattr(window.connections, "provider", lambda pid, *a, **k: FakeProvider(delay=0.05))
    _ask(qapp, panel, " ".join(["từ"] * 200))
    assert panel.btn_stop.isEnabled() and not panel.btn_send.isEnabled()
    assert _wait(qapp, lambda: "[TEST]" in panel.transcript.toPlainText())
    panel.btn_stop.click()
    assert _wait(qapp, lambda: panel.stream is None)
    assert window.budget.recent()[0]["status"] == "cancelled"
    assert panel.btn_send.isEnabled() and not panel.btn_stop.isEnabled()
    # Dừng giữa chừng: chưa nhận hết 200 từ
    reply = panel.transcript.toPlainText().split("🤖", 1)[1]
    assert "[TEST]" in reply and reply.count("từ") < 200


def test_provider_error_shown_and_question_dropped(qapp, window):
    panel = window.assistant
    _ask(qapp, panel, "lỗi nhé", model="fake-error")
    assert _wait(qapp, lambda: panel.stream is None)
    assert "429" in panel.usage_label.text() or "giới hạn" in panel.usage_label.text()
    assert panel.history == []
    assert window.budget.recent()[0]["status"] == "error"


def test_budget_blocks_and_unknown_price_confirmation(qapp, window, monkeypatch):
    from app_builder.agent.budget import Price
    panel = window.assistant
    warnings, questions = [], []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warnings.append(a[2]))
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: (questions.append(a[2]), QMessageBox.StandardButton.No)[1])
    window.budget.prices.set_user_price("fake", "fake-echo", Price(1000, 1000))
    window.budget.set_session_limit(0.01)
    _ask(qapp, panel, "đắt quá")
    assert warnings and panel.stream is None and panel.history == []
    # Model chưa có giá: hỏi xác nhận; trả lời Không thì không gửi
    window.budget.set_session_limit(None)
    _ask(qapp, panel, "model lạ", model="fake-unknown")
    assert questions and panel.stream is None and panel.history == []
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    panel.prompt.setPlainText("model lạ")
    panel.send()
    assert _wait(qapp, lambda: panel.stream is None)
    rec = window.budget.recent()[0]
    assert rec["model"] == "fake-unknown" and rec["cost_usd"] is None and rec["cost_known"] == 0


def test_history_saved_only_when_enabled(qapp, window):
    panel = window.assistant
    _ask(qapp, panel, "không lưu")
    assert _wait(qapp, lambda: panel.stream is None)
    assert window.db.query("SELECT COUNT(*) AS n FROM messages")[0]["n"] == 0
    window.settings.keep_message_history = True
    panel.new_chat()
    _ask(qapp, panel, "có lưu")
    assert _wait(qapp, lambda: panel.stream is None)
    rows = window.db.query("SELECT role, content FROM messages ORDER BY id")
    assert [r["role"] for r in rows] == ["user", "assistant"] and rows[0]["content"] == "có lưu"
    assert panel.hist_list.count() == 1


def test_connections_dialog_save_test_disconnect(qapp, window, monkeypatch):
    from app_builder.services.ai_connections import key_ref
    from app_builder.ui.connections_dialog import ConnectionsDialog
    dlg = ConnectionsDialog(window.connections, window)
    dlg.changed.connect(window._on_ai_changed)  # giống show_connections()
    assert set(dlg.cards) == {"openai", "deepseek", "gemini", "anthropic", "fake"}
    card = dlg.cards["openai"]
    card.key.setText("sk-test-ui-key-1234567890")
    card.base_url.setText("http://insecure.example.com")
    assert not card.save() and "Base URL" in card.result.text()
    assert not window.connections.is_connected("openai")
    card.base_url.setText("https://api.openai.com/v1")
    assert card.save()
    assert window.secrets.get(key_ref("openai")) == "sk-test-ui-key-1234567890"
    assert card.key.text() == "" and "sk-t" in card.key.placeholderText()
    assert window.assistant.provider.findData("openai") >= 0
    # Kiểm tra kết nối với provider TEST (chạy nền)
    fake = dlg.cards["fake"]
    fake.test()
    assert _wait(qapp, lambda: "✔" in fake.result.text())
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    card.disconnect()
    assert not window.connections.is_connected("openai") and window.secrets.get(key_ref("openai")) is None
    dlg.close()


def test_connection_test_reports_error_kind(qapp, window, monkeypatch):
    from app_builder.providers.base import ErrorKind, ProviderError
    from app_builder.ui.connections_dialog import ConnectionsDialog

    class Bad:
        def list_models(self):
            raise ProviderError(ErrorKind.auth, "401 invalid x-api-key", 401)

    dlg = ConnectionsDialog(window.connections, window)
    card = dlg.cards["anthropic"]
    monkeypatch.setattr(window.connections, "provider", lambda *a, **k: Bad())
    card.key.setText("sk-ant-wrong")
    card.test()
    assert _wait(qapp, lambda: "✖" in card.result.text())
    assert "API key" in card.result.text()
    dlg.close()


def test_usage_dialog_shows_records_and_saves_price(qapp, window):
    from app_builder.providers.base import Usage
    from app_builder.ui.usage_dialog import UsageDialog
    window.budget.record("r1", "anthropic", "claude-opus-5-5", Usage(1000, 500), "ok")
    dlg = UsageDialog(window.budget, None, None, window)
    assert dlg.history.rowCount() == 1 and dlg.history.item(0, 2).text() == "claude-opus-5-5"
    assert any(dlg.prices.item(i, 1).text() == "claude-opus-5-5" for i in range(dlg.prices.rowCount()))
    dlg.p_provider.setCurrentIndex(dlg.p_provider.findData("openai"))
    dlg.p_model.setText("gpt-test")
    dlg.p_in.setValue(1.25)
    dlg.p_out.setValue(10)
    dlg._save_price()
    assert window.budget.prices.lookup("openai", "gpt-test").output_per_m == 10
    dlg.session_budget.setValue(2.5)
    dlg._save_budget()
    assert window.budget.session_limit() == 2.5 and "2,5" in dlg.summary.text()
    dlg.close()
