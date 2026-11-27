# App Builder AI

IDE AI **local-first** chạy trên Windows 10/11: mô tả ý tưởng bằng tiếng Việt/Anh → tạo app mobile
**React Native + Expo + TypeScript + Expo Router** → xem trước → chỉnh sửa nhiều vòng → kiểm thử →
đẩy lên GitHub → xuất APK/AAB/IPA. Python (PySide6) chỉ điều khiển IDE, không phải runtime mobile.

> Trạng thái hiện tại: **M0 + M1 hoàn thành** (xem [PROGRESS.md](PROGRESS.md)). Các chức năng của milestone sau
> hiển thị rõ nhãn “Chưa triển khai — Mx” trong UI và bị vô hiệu hóa; không có nút giả.

## Yêu cầu

| Công cụ | Bắt buộc cho | Ghi chú |
|---|---|---|
| Python 3.11+ | IDE | |
| PySide6 6.6+ (kèm WebEngine) | IDE, preview nhúng | `pip install PySide6` |
| Node.js **LTS** (22.13+ / 24.3+ / 26+) | cài deps, preview, typecheck | Expo SDK 58 không khai báo hỗ trợ Node 25 |
| Git, GitHub CLI | GitHub (M5) | |
| JDK 17+, Android SDK, adb | build Android (M6) | Android Studio cài sẵn cả ba |
| Claude Code CLI, EAS CLI | tùy chọn (M7) | |

Chạy **Doctor** (nút trên Dashboard hoặc `python -m app_builder doctor`) để xem máy đang thiếu gì.

## Cài đặt & chạy

```powershell
.\scripts\setup.ps1      # tạo .venv, cài package (editable) + dev deps, chạy doctor
.\scripts\run.ps1        # mở ứng dụng
```

Hoặc thủ công:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m app_builder
```

Đóng gói desktop (PyInstaller onedir): `.\scripts\package.ps1` → `dist\AppBuilderAI\AppBuilderAI.exe`.

## Kiểm thử

```powershell
.venv\Scripts\python -m pytest -q                      # unit + integration offline + UI smoke (offscreen)
$env:APPBUILDER_RUN_SLOW="1"; .venv\Scripts\python -m pytest -q -m slow   # npm install + tsc thật cho 3 template (cần mạng)
```

Không cần API key để chạy test.

## Dữ liệu & bảo mật

- Dữ liệu IDE: `%LOCALAPPDATA%\AppBuilderAI\` (SQLite `appbuilder.db`, `settings.json`, `logs\` có rotate + che secret).
- Project mặc định: `Documents\AppBuilderAI\Projects` (đổi trong Cài đặt).
- Secret (API key, token) chỉ lưu trong **Windows Credential Manager** qua `keyring`; DB chỉ giữ key reference.
- Không telemetry. Không tự cài công cụ, không tự publish, không gọi dịch vụ tốn phí khi chưa xác nhận.
- Lần đầu cài dependencies/chạy project phải xác nhận **tin cậy workspace** (script npm có thể chạy mã tùy ý).
  Tiến trình con nhận môi trường tối giản, không có biến chứa KEY/TOKEN/SECRET.

## Cấu trúc

```
src/app_builder/
  core/       config, schemas, workspace (path safety), database (migrations), secret_store,
              process_manager (argv, Job Object), redaction, permissions, events, i18n
  services/   doctor, template_service, project_service, project_inspect
  ui/         main_window, dashboard, project_wizard, project_panel, editor_panel,
              assistant_panel, preview_panel, bottom_panel, doctor_dialog, settings_dialog, theme
  resources/  templates/ (_base, todo, education, blank, _sdk.json), i18n/ (vi, en)
tests/        unit/, integration/, ui/
docs/DECISIONS.md   decision log
```
