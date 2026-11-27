# Decision log

| # | Ngày | Quyết định | Lý do |
|---|---|---|---|
| D1 | 2026-11-27 | PySide6 Widgets + QSS tự viết (Fusion), không dùng thư viện theme ngoài | Nhẹ, ổn định, kiểm soát dark/light; không sao chép UI sản phẩm khác |
| D2 | 2026-11-27 | Expo **SDK 58** (`expo ~58.1.0`, RN 0.88.1, React 19.3, expo-router ~58.0.33, TS ~6.0.3) | Xác minh ngày 2026-11-27 từ npm registry: `expo@58.1.0/bundledNativeModules.json` + `expo-template-default@sdk-58`. Ghi trong `resources/templates/_sdk.json`, không hardcode từ trí nhớ |
| D3 | 2026-11-27 | package.json/app.json/brand.ts/i18n.ts **sinh bằng code**, file UI từ template `_base` + overlay | Một nguồn version duy nhất; escape JSON an toàn cho tên có dấu/ký tự đặc biệt |
| D4 | 2026-11-27 | Lockfile: chưa đưa `package-lock.json` vào template; lock được tạo ở lần `npm install` đầu trong project | Lockfile phụ thuộc registry tại thời điểm cài; project sinh ra commit lockfile của chính nó (M5 kiểm tra) |
| D5 | 2026-11-27 | Lưu local trong app sinh ra bằng `@react-native-async-storage/async-storage` 2.2.0 | Phiên bản do Expo SDK 58 khuyến nghị; chạy web + native không cần native build |
| D6 | 2026-11-27 | npm/npx chạy qua `node <npm-cli.js>` thay vì `npm.cmd` | Tránh cmd.exe và lỗi chèn lệnh với `.cmd`; `.cmd` khác chỉ chạy khi tham số qua kiểm tra ký tự đặc biệt |
| D7 | 2026-11-27 | Windows Job Object (KILL_ON_JOB_CLOSE) cho `process_manager.run`; QProcess dùng `taskkill /T /F` khi dừng | Dừng cả cây tiến trình (npm → node → esbuild...) |
| D8 | 2026-11-27 | Mọi project (kể cả tạo từ template) bắt đầu ở trạng thái **chưa tin cậy** | `npm install` chạy script của dependency → luôn cảnh báo trước lần cài/chạy đầu |
| D9 | 2026-11-27 | Xóa file trong explorer = chuyển vào Thùng rác (`QFile.moveToTrash`); gỡ project chỉ gỡ khỏi danh sách | Phương án ít phá hủy nhất |
| D10 | 2026-11-27 | Editor MVP = QPlainTextEdit + highlighter regex; Monaco local để sau | Theo đặc tả mục 6; không phụ thuộc CDN |
| D11 | 2026-11-27 | Lĩnh vực chưa có mẫu riêng dùng template `blank` + ghi yêu cầu vào spec | Không tạo template nửa vời; M8 thêm mẫu |
| D12 | 2026-11-27 | Quyền nhạy cảm (camera, vị trí, thông báo, login) chỉ ghi vào spec, `app.json` permissions rỗng | Mặc định không bật quyền nhạy cảm; agent M3 đề xuất patch để người dùng duyệt |
| D13 | 2026-11-27 | i18n IDE bằng JSON `resources/i18n/{vi,en}.json`, đổi ngôn ngữ cần khởi động lại | Đơn giản, đủ cho MVP |
| D14 | 2026-11-27 | Doctor cảnh báo Node lẻ/ngoài `engines` của Expo, không chặn | Máy hiện dùng Node 25.9 (non-LTS); `npm install` + `tsc` + `expo export --platform web` vẫn chạy được nhưng có cảnh báo EBADENGINE |
| D15 | 2026-11-27 | Provider dùng **SDK chính thức** (`openai` ≥ 3.60, `anthropic` ≥ 2.14, `google-genai` ≥ 3.6), chuyển từ extra `ai` vào dependencies chính; DeepSeek dùng SDK `openai` với base URL riêng | SDK xử lý retry/stream/lỗi có kiểu; M2 là chức năng lõi nên `setup.ps1` (`.[dev]`) phải cài đủ. Adapter nhận `client` để test bằng client giả |
| D16 | 2026-11-27 | Chỉ ghi sẵn giá Claude (có nguồn + ngày); giá OpenAI/Gemini/DeepSeek do người dùng nhập; model chưa có giá phải xác nhận trước khi gửi | Không hardcode giá từ trí nhớ; giá các hãng đổi thường xuyên |
| D17 | 2026-11-27 | Claude: bật dự phòng phía server khi model từ chối (`server-side-fallback-2026-07-01`, `fallbacks="default"`) cho Opus 5/5.5, Sonnet 5.5, Fable 5.1/5.2 | Khuyến nghị của tài liệu Claude API; lượt chạy model dự phòng tính giá model đó → ghi “≈ ước tính” |
| D18 | 2026-11-27 | `max_output_tokens` theo chế độ trong spec: Tiết kiệm 4 000 · Cân bằng 16 000 · Nâng cao 64 000 | Tránh cắt câu trả lời nhưng vẫn giữ mức giữ chỗ ngân sách hợp lý |
| D19 | 2026-11-27 | Base URL tùy chỉnh chỉ `https://` tới host công khai (chặn http, user:pass@, query/fragment, localhost, IP nội bộ) | Không gửi API key qua kênh không mã hóa hoặc tới máy trong mạng nội bộ do nhập nhầm/bị lừa |
| D20 | 2026-11-27 | Streaming chạy trên QThread riêng, hủy bằng `CancelToken`; ghi DB và cập nhật UI trên luồng UI | UI không bị treo; tránh race khi ghi `usage_records` |
| D21 | 2026-11-27 | Key lưu trong keyring với ref `ai.<provider>.api_key`; base URL trong bảng `settings`; danh sách model trong `model_cache` | Đúng nguyên tắc M0: DB chỉ giữ reference, không giữ secret |
| D22 | 2026-11-27 | Provider TEST (`fake`) chỉ hiện khi `APPBUILDER_FAKE_PROVIDER=1` | Test/demo offline không gọi mạng; người dùng thường không thấy |
| D23 | 2026-11-27 | Nội dung chat chỉ lưu vào `conversations/messages` khi bật “Lưu lịch sử” trong Cài đặt; `usage_records` luôn ghi nhưng không chứa nội dung | Riêng tư theo mặc định, vẫn theo dõi được chi phí |
| D24 | 2026-11-27 | Ngoài Windows, tiến trình con chạy trong session riêng; `kill_tree` không killpg nhóm của chính app | Sửa lỗi diệt nhầm App Builder khi timeout/Dừng trên Linux/macOS |
