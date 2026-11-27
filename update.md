# Cập nhật cho phiên App Builder trên máy Windows

Ngày 2026-11-27. File này do phiên Claude Code trên cloud viết; phiên đó đã làm việc với repo `HeriSoft/ios` qua GitHub.

## 1. Tóm tắt: M2 đã xong và đã vào `main`

- **M2 đã được gộp vào `main`** qua PR #2 (https://github.com/HeriSoft/ios/pull/2), merge commit `a0d7464`.
- Máy Windows đã chuyển sang `main` mới nhất: `D:\Developer\ios` đang ở `a0d7464`, venv đã cài `openai` 3.60.0, `anthropic` 2.14.0 và `google-genai` 3.6.1.
- **Đừng làm lại M2.** Việc tiếp theo là M3 (mục 6), sau khi xong 2 việc nhỏ ở mục 4.

## 2. Bản M2 dở dang của phiên Windows đã được cất ở đâu

Phần M2 đang làm dở, chưa commit (`providers/`, `agent/`, `connections_dialog.py`, `usage_panel.py`, `async_runner.py`, `pricing.json` và 4 file đã sửa) chặn `git pull`. Vì vậy nó đã được commit sang nhánh riêng:

- Nhánh **`m2-windows-wip`**, commit `67a9aaf` ("WIP: M2 tu phien Windows (chua hoan thanh)"), đã đẩy lên GitHub.
- Trên `main` không còn file nào của bản này. **Không merge nguyên nhánh này vào `main`**: nó trùng chức năng với bản đã gộp và không có test. Chỉ lấy 2 phần ghi ở mục 4.

## 3. Nội dung M2 trên `main`

Xem chi tiết trong `app-builder/PROGRESS.md` (mục "M2") và `app-builder/docs/DECISIONS.md` (D15–D24). Tóm tắt:

- `providers/base.py`: `AIProvider` (`list_models()`, `stream(AIRequest, CancelToken)` phát `TextDelta…` rồi `Done(usage, stop_reason, model, fallback_used)`), `ProviderError(kind)`, `validate_base_url()` (chỉ https tới host công khai), `PROVIDERS`.
- Adapter dùng SDK chính thức: `openai_provider.py` (Responses API, `store=False`), `deepseek_provider.py` (SDK `openai` + Chat Completions), `gemini_provider.py` (`google-genai`), `anthropic_provider.py` (`messages.stream`; mặc định `claude-opus-5-5`; với Opus 5/5.5, Sonnet 5.5, Fable 5.1/5.2 thì bật dự phòng phía server `server-side-fallback-2026-07-01` + `fallbacks="default"`), `fake_provider.py` (nhãn TEST, chỉ hiện khi `APPBUILDER_FAKE_PROVIDER=1`), `factory.py`.
- `services/ai_connections.py`: key lưu trong keyring với ref `ai.<provider>.api_key`; base URL lưu trong bảng `settings`; danh sách model lưu trong `model_cache`.
- `agent/budget.py`: `PriceBook` (chỉ có sẵn giá Claude; giá hãng khác do người dùng nhập, lưu trong `settings` key `ai.prices`), ước lượng và giữ chỗ trước request, chặn khi vượt ngân sách phiên/dự án, cảnh báo ≥ 80%, ghi sổ `usage_records`.
- UI: `ui/ai_worker.py` (QThread + `CancelToken`), `ui/connections_dialog.py`, `ui/usage_dialog.py`; `assistant_panel.py` đã có chat streaming, nút Dừng, chi phí từng lượt, lịch sử (chỉ lưu khi bật trong Cài đặt); `main_window.py` có các nút "🔌 Kết nối AI", "$ Chi phí AI" và badge ngân sách.
- Test: Linux 117 passed; Windows CI 120 passed, 5 skipped. Test gọi API thật `tests/integration/test_live_providers.py` (`pytest -m live`, cần `APPBUILDER_LIVE_<PROVIDER>_KEY`) đang **BLOCKED** vì chưa có key.
- **Sửa lỗi M0:** trên Linux/macOS, `process_manager.run` và `ProcessRunner` từng `os.killpg` nhầm process group của chính App Builder khi timeout hoặc bấm Dừng. Nay tiến trình con chạy trong session riêng. Windows không bị ảnh hưởng.

## 4. Hai việc nên làm trước M3 (lấy từ `m2-windows-wip`)

Bản Windows làm 2 phần này tốt hơn bản trên `main`. Mỗi phần nên làm kèm test:

1. **Bảo mật base URL tùy chỉnh (ưu tiên cao).** Bản trên `main` có **lỗ hổng**: khi đổi base URL sang một host không chính thức, app vẫn gửi **API key chính thức** tới host đó.
   - Áp dụng cách của `m2-windows-wip:app-builder/src/app_builder/providers/registry.py`: `official_hosts`, key ref gắn với host (`provider:<id>@<host>`) cho endpoint tùy chỉnh, và cảnh báo khi dùng host không chính thức.
   - Sửa trong `services/ai_connections.py` (`key_ref`, `save`, `api_key`, `provider`) và `ui/connections_dialog.py`.
   - Test bắt buộc: key của host chính thức không bao giờ được dùng khi base URL trỏ tới host khác.
2. **Bảng giá OpenAI / DeepSeek / Gemini.** Lấy từ `m2-windows-wip:app-builder/src/app_builder/resources/pricing.json` (có nguồn, ngày đọc 2026-11-27, giá theo `effective_from`, giới hạn `max_prompt_tokens`).
   - Nạp vào `PriceBook` trong `agent/budget.py`. Giữ thứ tự ưu tiên: giá người dùng nhập > bảng giá có sẵn.
   - Hỗ trợ `effective_from` (chọn mức giá theo ngày gửi request) và prompt vượt `max_prompt_tokens` coi như giá chưa biết (hỏi xác nhận).
   - Cập nhật `usage.prices_note` trong `vi.json` / `en.json`, vì câu đó đang nói "không ghi sẵn giá OpenAI/Gemini/DeepSeek".
   - Ghi lại thành quyết định mới trong DECISIONS.md, thay cho D16.

## 5. Việc lặt vặt

- **Sửa đường dẫn trong `app-builder/PROGRESS.md` dòng 7.** Trên `main` có một ký tự điều khiển ẩn (BEL, `\x07`): `\a` trong `D:\Developer\ios\app-builder` bị biến thành BEL, nên hiển thị thành `iospp-builder`. Đường dẫn đúng là `D:\Developer\ios\app-builder`. Bản sửa đã có ở nhánh `claude/github-connection-st7sj4` (commit `13a9994`) nhưng chưa vào `main`: sửa thẳng trên `main` hoặc cherry-pick commit đó. Khi viết đường dẫn Windows bằng script Python, nhớ dùng raw string.
- Câu "workflow iOS của repo chạy với mọi push ngoài `android/`" ở dòng 7 PROGRESS đã cũ, xem mục 7.

## 6. M3 (việc tiếp theo, theo PROGRESS.md)

- Agent plan → diff → apply dựa trên lớp provider của M2. Model trả `ChangePlan` / `FileChange` (đã có trong `core/schemas.py`); xem diff; áp dụng nguyên tử, có checkpoint và hoàn tác; giới hạn số vòng tự sửa lỗi.
- Mở khóa các nút Lập kế hoạch / Tạo / Chỉnh sửa / Sửa lỗi / Áp dụng / Từ chối / Hoàn tác trong `assistant_panel.py` (biến `ACTIONS`).
- Nạp lại hội thoại đã lưu vào ngữ cảnh chat; chọn phạm vi (app / màn hình / file / component).

## 7. CI và cách làm việc chung trong repo

- Repo này chứa **3 dự án**: `CalorieScan/` (app iOS Swift), `android/` (app Android Kotlin) và `app-builder/`. Phiên App Builder **không sửa** hai thư mục kia.
- Workflow:
  - **App Builder tests** (`.github/workflows/app-builder.yml`): chạy trên `windows-latest`, chỉ khi `app-builder/**` thay đổi, khoảng 2 phút.
  - **iOS build & test**: chạy trên macOS (đắt). Nay đã **bỏ qua** `app-builder/**`, nên đẩy code App Builder không còn tốn phút macOS.
  - **Android build & test**: chỉ chạy khi `android/**` thay đổi.
- Commit chỉ sửa tài liệu nên thêm `[skip ci]` vào message.
- Hai phiên Claude (Windows và cloud) cùng làm trên repo này. Trước khi bắt đầu việc mới: `git pull`. Chỉ một phiên làm mỗi việc, và commit, đẩy lên thường xuyên, để không xảy ra lại chuyện hai bản M2 song song.
