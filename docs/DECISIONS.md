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
