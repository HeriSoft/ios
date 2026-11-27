# PROGRESS — App Builder AI

Tài liệu duy trì ngữ cảnh giữa các phiên làm việc. Đặc tả gốc: `app_builder.md` (bản người dùng cung cấp).
Quy ước: chỉ ghi **PASS** khi đã thực sự chạy; **BLOCKED** khi máy thiếu công cụ/tài khoản; **TODO** khi chưa làm.

**Repository chính:** https://github.com/HeriSoft/ios — thư mục `app-builder/` (repo PUBLIC, chung với dự án CalorieScan).
Làm việc tại bản clone `D:\Developer\ios\app-builder`. Đẩy CI: workflow iOS của repo chạy với mọi push ngoài `android/`.
Bản sao cũ `HeriSoft/app-builder-ai` (private) và thư mục `D:\Developer\App Builder` chỉ còn là lưu trữ, không cập nhật tiếp.

## Tổng quan milestone

| Mốc | Nội dung | Trạng thái |
|---|---|---|
| M0 | Doctor, cấu trúc repo, Python env, README, decision log | ✅ Hoàn thành (2026-11-27) |
| M1 | Desktop UI, dashboard, wizard, workspace, template Todo + Giáo dục, local data | ✅ Hoàn thành (2026-11-27) |
| M2 | 4 API adapter, model picker, streaming, test connection, secure keys, usage budget | ✅ Hoàn thành (2026-11-27) — gọi API thật: BLOCKED (chưa có key) |
| M3 | Agent plan/diff/apply, editor, checkpoint/undo, bounded repair | ⏳ Tiếp theo |
| M4 | Expo web live preview, device frames, review/typecheck, terminal logs, QR/device | TODO |
| M5 | GitHub private/public wizard, secret scan, source ZIP | TODO |
| M6 | Android local APK/AAB, build center, signing wizard, adb install | TODO (máy hiện BLOCKED: thiếu JDK/Android SDK/adb) |
| M7 | Claude Code CLI, Claude Desktop handoff, EAS Android/iOS | TODO |
| M8 | Thêm template, visual edit, backend tùy chọn, installer Windows, regression | TODO |

## Môi trường đã kiểm tra (2026-11-27)

Windows 10 Pro 19045 x64 · RAM 16 GB · Python 3.11.7 · PySide6 6.12.0 (có WebEngine) · Node **25.9.0** (non-LTS)
· npm 11.12.1 · Git 2.55 · gh 2.105 (đã đăng nhập) · keyring WinVault ✔
· **Thiếu**: JDK, Android SDK, adb (→ build Android BLOCKED) · Claude Code CLI, EAS CLI (tùy chọn).
Ổ C còn ~29 GB (workspace mặc định nằm ở Documents trên C:).

## M0 — Nền tảng

File: `pyproject.toml`, `.gitignore`, `README.md`, `docs/DECISIONS.md`, `scripts/{setup,run,package}.ps1` (UTF-8 BOM cho PS 5.1),
`src/app_builder/{__init__,__main__,bootstrap}.py`, `core/*`, `services/doctor.py`.

- Doctor (GUI + CLI `python -m app_builder doctor [--json]`): Python, PySide6, WebEngine, Node (+ kiểm tra `engines` Expo),
  npm, Git, gh (+ auth status), JDK, Android SDK, adb, Claude CLI, EAS CLI, keyring, RAM, dung lượng; hướng dẫn cài + danh sách BLOCKED.
- Core: config (Pydantic, `%LOCALAPPDATA%\AppBuilderAI`), SQLite + migration (11 bảng theo đặc tả), path safety
  (traversal, ổ đĩa, UNC, ADS, tên thiết bị, symlink/junction), ghi file nguyên tử, secret store (keyring/memory-only),
  redaction log, process manager (argv, shell=False, timeout, env tối giản, Job Object, launcher an toàn cho npm/.cmd),
  permissions/trust, event bus, i18n.

## M1 — Desktop UI + project + template

File: `ui/{main_window,dashboard,project_wizard,project_panel,editor_panel,assistant_panel,preview_panel,bottom_panel,
doctor_dialog,settings_dialog,process_runner,theme,widgets}.py`, `services/{template_service,project_service,project_inspect}.py`,
`resources/templates/{_sdk.json,_base,todo,education,blank}`, `resources/i18n/{vi,en}.json`.

Chức năng thật:
- **Dashboard**: dự án gần đây (card), tìm kiếm, tạo mới, mở/import thư mục (đánh dấu chưa tin cậy), nhân bản
  (bỏ node_modules), mở Explorer, gỡ khỏi danh sách (xác nhận; không xóa file), trạng thái thư mục mất / build cuối.
- **Wizard 5 bước**: tên/mô tả/package ID/bundle ID (tự sinh + validate)/thư mục/ngôn ngữ/nền tảng → 12 lĩnh vực
  (chọn nhiều, gợi ý mẫu) + chức năng + 5 phong cách UI → lưu trữ/backend/quyền (nhạy cảm mặc định tắt) → provider/model/
  chế độ/ngân sách (lưu vào spec) → prompt + ảnh/tài liệu tham chiếu (≤5 MB, chép vào `.appbuilder/references`) → Tạo.
- **Template Expo SDK 58** (TypeScript, Expo Router, theme sáng/tối lưu lại, i18n vi/en, loading/empty/error, responsive
  maxWidth): **Todo** 3 màn hình CRUD AsyncStorage; **Giáo dục** 4 tab + chi tiết bài học + cài đặt, tiến độ local;
  **Blank** cho lĩnh vực chưa có mẫu.
- **Workspace IDE**: toolbar theo bố cục đặc tả; panel Project (Files tree ẩn node_modules/.git, tìm tên + nội dung,
  tạo/đổi tên/xóa→Thùng rác có path check; Screens từ Expo Router; Assets import + kích thước + license; Data/APIs từ spec;
  Dependencies từ package.json + bản đã cài + nút `npm install` có xác nhận trust); Code editor (tabs, số dòng,
  highlight TS/JSON/CSS/Python/MD, dirty state, Ctrl+S, lưu nguyên tử, phát hiện thay đổi ngoài IDE bằng SHA256 + hỏi
  ghi đè/tải lại); Terminal stream output + Dừng cả cây; Tasks từ bảng `jobs`; theme dark/light; Settings (ngôn ngữ, theme,
  workspace, đường dẫn công cụ, xóa cache/history).
- Chưa triển khai và **đã gắn nhãn rõ + vô hiệu hóa**: AI chat/plan (M2–M3), Diff (M3), Preview live (M4), Review/Problems (M4),
  Git/GitHub (M5), Build/Export (M5–M7), AI Usage/Budget (M2), backend Supabase/Firebase/REST (M8).

## M2 — Provider AI, streaming, kết nối, ngân sách

Làm trong phiên Claude Code cloud (Linux, Qt offscreen); trước khi làm tiếp trên máy Windows: `git pull`.

File mới: `providers/{base,_errors,factory,openai_provider,deepseek_provider,gemini_provider,anthropic_provider,fake_provider}.py`,
`agent/budget.py`, `services/ai_connections.py`, `ui/{ai_worker,connections_dialog,usage_dialog}.py`;
sửa `ui/{assistant_panel,main_window}.py`, `resources/i18n/{vi,en}.json` (+85 khóa), `pyproject.toml`.

- **Giao diện chung** `AIProvider`: `list_models()` + `stream(AIRequest, CancelToken)` phát `TextDelta…` rồi `Done(usage, stop_reason,
  model, fallback_used)`; lỗi chuẩn hóa `ProviderError(kind)` (auth / permission / not_found / rate_limit / invalid_request /
  server / network / timeout) — chi tiết lỗi đã che secret.
- **Adapter dùng SDK chính thức** (D15): OpenAI — Responses API (`store=False`); DeepSeek — SDK `openai` + Chat Completions
  (`stream_options.include_usage`); Gemini — `google-genai` `generate_content_stream` (token suy nghĩ tính vào đầu ra);
  Claude — `anthropic` `messages.stream`, model mặc định `claude-opus-5-5`, bật dự phòng phía server khi model từ chối
  (`fallbacks="default"`, D17). Usage chuẩn hóa: input gồm cả phần cache, cached tách riêng, output gồm token suy luận.
- **Kết nối AI** (toolbar “Kết nối AI” hoặc ⚙ trong Assistant): key ẩn/hiện, lưu bằng keyring (`ai.<provider>.api_key`),
  không bao giờ ghi vào settings/SQLite/log; base URL chỉ `https://` tới host công khai (chặn http, user:pass@, query, localhost,
  IP nội bộ); Kiểm tra kết nối (chạy nền) = tải danh sách model → cache vào `model_cache`; Ngắt kết nối xóa key + cache.
- **Assistant › Chat**: chọn provider đã kết nối + model (danh sách đã cache hoặc gõ id), streaming trên QThread, nút **Dừng**
  hủy giữa chừng, cuộc trò chuyện mới, system prompt từ spec dự án; mỗi lượt hiện token vào/cache/ra + chi phí; báo khi bị cắt
  token, model từ chối, dùng model dự phòng. Lịch sử chỉ lưu khi bật trong Cài đặt (D23). Lập kế hoạch/sửa file vẫn khóa (M3).
- **Ngân sách** (`agent/budget.py`): bảng giá có nguồn + ngày; giá Claude lấy từ tài liệu Claude API (2026-11-03); giá
  OpenAI/Gemini/DeepSeek không ghi sẵn — người dùng nhập trong “Chi phí AI › Bảng giá” (D16), model chưa có giá phải xác nhận
  trước khi gửi. Trước request: ước lượng chi phí tối đa (đầu vào ước lượng + `max_output_tokens` theo chế độ, D18) và giữ chỗ;
  chặn khi vượt ngân sách phiên/dự án, cảnh báo ≥ 80 %. Sau request: ghi `usage_records` (không lưu nội dung chat), lượt bị
  dừng/lỗi cũng ghi. Toolbar hiện “Phiên: $đã dùng / $giới hạn”.
- **Provider TEST** (`fake`, nhãn rõ “TEST”): không gọi mạng, chỉ hiện khi `APPBUILDER_FAKE_PROVIDER=1` (test/demo, D22).
- **Sửa lỗi M0 phát hiện khi chạy test trên Linux**: `process_manager.run`/`ProcessRunner` khởi chạy tiến trình con chung process
  group với app, nên khi timeout/Dừng thì `os.killpg` diệt luôn App Builder (và pytest). Nay tiến trình con có session riêng và
  `kill_tree` không bao giờ killpg nhóm của chính app. (Windows dùng Job Object/taskkill — không bị ảnh hưởng.)
- **CI**: workflow `App Builder tests` chạy pytest trên `windows-latest` (Qt offscreen) cho thay đổi trong `app-builder/`;
  workflow iOS (macOS) bỏ qua `app-builder/**` nên đẩy code App Builder không còn tốn ~15 phút máy macOS.

## Bằng chứng kiểm thử

| Test | Kết quả | Bằng chứng |
|---|---|---|
| `pytest -q` (unit + integration offline + UI smoke offscreen) | **PASS** 78 passed, 1 skipped (slow opt-in) | chạy 2026-11-27, ~9 s |
| Path traversal: `..`, tuyệt đối, ổ đĩa, UNC, ADS, CON/NUL, symlink, junction | **PASS** | `tests/unit/test_workspace.py` |
| Redaction, migration/rollback, schema, secret store, env tối giản, `.cmd` an toàn, timeout kill | **PASS** | `tests/unit/test_core_misc.py` |
| Sinh 3 template vào đường dẫn có dấu + khoảng trắng; version khớp `_sdk.json`; khóa i18n đủ | **PASS** | `tests/integration/test_templates_projects.py` |
| Vòng đời project: tạo, tìm, nhân bản, gỡ (giữ file), import (untrusted), audit | **PASS** | như trên |
| UI: wizard tạo project tiếng Việt, mở workspace, validate, editor lưu + xung đột, QProcess npm, dừng tiến trình, đổi theme, Doctor | **PASS** | `tests/ui/test_ui_smoke.py` |
| `npm install` + `tsc --noEmit` cho template Todo / Giáo dục / Blank | **PASS** (thủ công) | 521 packages, tsc exit 0 ×3 (Node 25 cảnh báo EBADENGINE) |
| `npx expo export --platform web` template Todo | **PASS** (thủ công) | bundle `entry-*.js` 1.1 MB, `dist-web/index.html` |
| Test slow tự động (`APPBUILDER_RUN_SLOW=1 pytest -m slow`): npm install + tsc ×3 template, đường dẫn có dấu | **PASS** | 1 passed in 107.95 s (2026-11-27) |
| Doctor CLI trên máy thật | **PASS** | 16 mục; BLOCKED: Android build, Emulator, Cài APK, Thiết bị USB |
| Ảnh chụp UI dark/light (offscreen) | **PASS** | dashboard, wizard, workspace — kiểm tra bằng mắt |
| Chạy app thật trên Android/emulator, CRUD sau restart trên thiết bị | **BLOCKED** | thiếu Android SDK/adb; cần M4/M6 |
| M2 · `pytest -q` toàn bộ (Linux, Python 3.13, PySide6 6.12, Qt offscreen) | **PASS** 117 passed, 8 skipped (4 chỉ chạy trên Windows, 4 live) | phiên cloud 2026-11-27, ổn định 3 lần chạy |
| M2 · Adapter 4 provider với client giả: streaming, usage (cache/suy luận), hủy, dự phòng Claude, lọc model, lỗi→kind, che key trong lỗi | **PASS** | `tests/unit/test_providers.py` |
| M2 · Base URL (https, host công khai), giá, ngân sách 80 %/chặn, giữ chỗ, sổ chi phí, key chỉ trong secret store | **PASS** | `tests/unit/test_budget_connections.py` |
| M2 · UI: chat streaming, Dừng, lỗi 429, chặn ngân sách, xác nhận giá chưa biết, lịch sử bật/tắt, hộp thoại Kết nối/Chi phí | **PASS** | `tests/ui/test_ai_m2.py` (provider TEST) |
| M2 · Ảnh chụp UI (dark, offscreen): Assistant chat, Kết nối AI, Chi phí AI | **PASS** | kiểm tra bằng mắt trong phiên cloud |
| M2 · Gọi API thật OpenAI / DeepSeek / Gemini / Claude | **BLOCKED** | chưa có key; chạy `APPBUILDER_LIVE_<PROVIDER>_KEY=… pytest -m live` |
| M2 · `pytest -q` trên Windows thật (Python 3.11.9, PySide6 6.12, keyring WinVault) | **PASS** 120 passed, 5 skipped (4 live, 1 slow) | GitHub Actions `App Builder tests` run #2, windows-latest, 2026-11-27 |

## Known issues / hạn chế thực tế

1. Node 25.9 là bản non-LTS, nằm ngoài `engines` của Expo SDK 58 → npm cảnh báo EBADENGINE. Khuyến nghị cài Node 24 LTS.
2. Chưa có `package-lock.json` trong template; lock sinh ra ở lần `npm install` đầu (D4).
3. Dừng tiến trình QProcess dùng `taskkill /T /F` (chưa gán Job Object cho QProcess như `process_manager.run`).
4. Tìm kiếm trong project quét tối đa 20.000 file / 200 kết quả.
5. Đổi ngôn ngữ IDE cần khởi động lại.
6. Highlighter regex đơn giản (MVP), chưa có Monaco.
7. Thư mục Files tree dùng QFileSystemModel; file ẩn `.appbuilder` vẫn hiện (có chủ đích).
8. Ước lượng token trước request là thô (~3 ký tự/token, thiên về cao) — chỉ dùng để giữ chỗ ngân sách; chi phí thật lấy từ usage.
9. Giá Claude Haiku 5.5 dùng mức cho prompt ≤ 100K token; ghi cache (cache write) tính như đầu vào thường (thực tế đắt hơn ~25 %).
10. Lượt dùng model dự phòng của Claude, hoặc bị Dừng trước khi có usage, ghi chi phí “≈ ước tính” (`cost_known = 0`).
11. Lịch sử hội thoại M2 chỉ để xem lại; chưa nạp lại hội thoại cũ vào ngữ cảnh chat (M3).

## Cách mở app

```powershell
.\scripts\setup.ps1   # lần đầu
.\scripts\run.ps1
```

## Việc tiếp theo (M3)

- Agent plan → diff → apply trên `ProviderLayer` của M2: model trả `ChangePlan`/`FileChange` (schemas đã có), xem diff,
  áp dụng nguyên tử có checkpoint/undo, giới hạn số vòng sửa lỗi (bounded repair).
- Mở khóa các nút Lập kế hoạch / Tạo / Chỉnh sửa / Sửa lỗi / Áp dụng / Từ chối / Hoàn tác trong Assistant.
- Nạp lại hội thoại đã lưu vào ngữ cảnh; chọn phạm vi (app / màn hình / file / component).
