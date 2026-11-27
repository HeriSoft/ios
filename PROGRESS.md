# PROGRESS — App Builder AI

Tài liệu duy trì ngữ cảnh giữa các phiên làm việc. Đặc tả gốc: `app_builder.md` (bản người dùng cung cấp).
Quy ước: chỉ ghi **PASS** khi đã thực sự chạy; **BLOCKED** khi máy thiếu công cụ/tài khoản; **TODO** khi chưa làm.

## Tổng quan milestone

| Mốc | Nội dung | Trạng thái |
|---|---|---|
| M0 | Doctor, cấu trúc repo, Python env, README, decision log | ✅ Hoàn thành (2026-11-27) |
| M1 | Desktop UI, dashboard, wizard, workspace, template Todo + Giáo dục, local data | ✅ Hoàn thành (2026-11-27) |
| M2 | 4 API adapter, model picker, streaming, test connection, secure keys, usage budget | ⏳ Tiếp theo |
| M3 | Agent plan/diff/apply, editor, checkpoint/undo, bounded repair | TODO |
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

## Known issues / hạn chế thực tế

1. Node 25.9 là bản non-LTS, nằm ngoài `engines` của Expo SDK 58 → npm cảnh báo EBADENGINE. Khuyến nghị cài Node 24 LTS.
2. Chưa có `package-lock.json` trong template; lock sinh ra ở lần `npm install` đầu (D4).
3. Dừng tiến trình QProcess dùng `taskkill /T /F` (chưa gán Job Object cho QProcess như `process_manager.run`).
4. Tìm kiếm trong project quét tối đa 20.000 file / 200 kết quả.
5. Đổi ngôn ngữ IDE cần khởi động lại.
6. Highlighter regex đơn giản (MVP), chưa có Monaco.
7. Thư mục Files tree dùng QFileSystemModel; file ẩn `.appbuilder` vẫn hiện (có chủ đích).

## Cách mở app

```powershell
.\scripts\setup.ps1   # lần đầu
.\scripts\run.ps1
```

## Việc tiếp theo (M2)

- `providers/base.py` (Protocol AIProvider, AIRequest/AIEvent), adapter OpenAI (Responses API), DeepSeek (OpenAI-compatible),
  Gemini (`google-genai`), Anthropic (Messages API) — kiểm tra docs/flags hiện hành trước khi viết.
- `ui/connections_dialog.py`: card provider, key mask/show (keyring), base URL + validate HTTPS/host, Test Connection,
  Refresh Models, Disconnect.
- `agent/budget.py`: bảng giá có ngày cập nhật, ước lượng trước request, ledger `usage_records`, cảnh báo 80%, reservation,
  giá unknown → hỏi xác nhận.
- Streaming + cancel trong Assistant panel; fake provider có nhãn TEST cho test offline; test tích hợp thật opt-in → BLOCKED nếu không có key.
