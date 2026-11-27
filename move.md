# Chuyển App Builder về repo riêng (private)

Người dùng đã chọn: **App Builder AI quay về thư mục `D:\Developer\App Builder` và repo private `HeriSoft/app-builder-ai`**, và từ nay làm việc ở đó. Lý do: repo `HeriSoft/ios` là public, còn code App Builder cần giữ kín.

Hiện tại code mới nhất (M0 + M1 + M2) chỉ có ở `D:\Developer\ios\app-builder`. Thư mục `D:\Developer\App Builder` vẫn dừng ở M1.

## Bước 0: Làm xong việc đang dở, không để mất gì

1. Hoàn thành việc đang làm (bảng giá, sửa bảo mật base URL, PROGRESS/DECISIONS). Chạy toàn bộ test.
   Nếu `pytest` chạy quá vài phút, có thể bị treo do một `QMessageBox` bật lên trong test: hãy monkeypatch hộp thoại đó như trong `tests/ui/test_ai_m2.py`.
2. Commit và push lên `HeriSoft/ios` `main`, để có một mốc an toàn trước khi chuyển.

## Bước 1: Kiểm tra thư mục đích

```bat
cd /d "D:\Developer\App Builder"
git status
git remote -v
```

- `git remote -v` phải trỏ tới `HeriSoft/app-builder-ai`.
- Nếu `git status` có thay đổi chưa commit thì **dừng lại và hỏi người dùng**, không ghi đè.

## Bước 2: Chép code mới nhất sang (không chép .git, .venv, cache)

```bat
robocopy "D:\Developer\ios\app-builder" "D:\Developer\App Builder" /E /XD .git .venv .pytest_cache __pycache__ /XF *.pyc
```

- Không dùng `/MIR`: lệnh đó xóa file ở đích và dễ đụng vào `.git` hoặc `.venv` của thư mục cũ.
- Sau khi chép, chạy `git status` trong `D:\Developer\App Builder`. Với file nào **chỉ có ở thư mục cũ** (đã bị xóa hoặc đổi tên trong bản mới), xem lại từng file rồi mới `git rm`.
- So sánh nhanh để chắc chắn hai bên giống nhau, ngoài `.git`, `.venv` và cache: `git diff --no-index --stat "D:\Developer\ios\app-builder\src" "D:\Developer\App Builder\src"` phải không còn khác biệt.

## Bước 3: CI cho repo riêng

Chép `D:\Developer\ios\.github\workflows\app-builder.yml` sang `D:\Developer\App Builder\.github\workflows\app-builder.yml`, rồi sửa lại vì code giờ nằm ở gốc repo:

- Bỏ khối `paths:` (hoặc đổi `app-builder/**` thành `**`).
- Bỏ `defaults: run: working-directory: app-builder`.

Lưu ý: repo private dùng hạn mức phút GitHub Actions của tài khoản, và máy Windows tính gấp đôi máy Linux. Mỗi lần chạy khoảng 2 phút nên vẫn rất ít.

## Bước 4: Cập nhật tài liệu

Trong `PROGRESS.md`, sửa phần "Repository chính" (dòng 6–8) thành:

- Repository chính: `HeriSoft/app-builder-ai` (private), làm việc tại `D:\Developer\App Builder`.
- Bản trong `HeriSoft/ios/app-builder` là bản cũ, sẽ bị gỡ khỏi repo public.

Thêm quyết định mới vào `docs/DECISIONS.md`: chuyển App Builder về repo private vì repo `ios` là public.

**Chú ý ký tự `\` khi ghi đường dẫn Windows bằng script Python.** Phải dùng raw string `r"D:\Developer\App Builder"`. Trước đây `\a` trong `D:\Developer\ios\app-builder` đã bị biến thành ký tự BEL ẩn.

## Bước 5: Cài lại môi trường, test, đẩy lên

```bat
cd /d "D:\Developer\App Builder"
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
.venv\Scripts\python -m pytest -q
git add -A
git commit -m "Đồng bộ M2 từ HeriSoft/ios: provider AI, chat streaming, kết nối, ngân sách + CI Windows"
git push
```

- `setup.ps1` phải cài `openai`, `anthropic` và `google-genai`. Kết quả mong đợi khi chạy test: tất cả đều pass (trên Windows CI trước đó là 120 passed, 5 skipped, cộng thêm các test mới của bảng giá và base URL).
- Mở app bằng `.\scripts\run.ps1` và kiểm tra có nút "🔌 Kết nối AI" và "$ Chi phí AI".

## Bước 6: Báo lại người dùng, chưa xóa gì trong repo `ios`

- Báo người dùng khi bước 5 xong (kèm số test pass và link commit trên `app-builder-ai`).
- **Không tự xóa** thư mục `app-builder/` trong `HeriSoft/ios`. Việc gỡ nó khỏi repo public, cùng file `.github/workflows/app-builder.yml` và dòng `app-builder/**` trong `ios.yml`, sẽ do người dùng quyết định. Nhắc người dùng rằng gỡ thư mục không xóa code khỏi lịch sử git của repo public.
- Từ nay phiên này chỉ làm App Builder trong `D:\Developer\App Builder`.
