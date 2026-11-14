# Quét Calo (CalorieScan)

Ứng dụng iOS (SwiftUI) quét mã vạch / mã QR / nhãn dinh dưỡng trên bao bì sản phẩm và tính lượng calo.

## Tính năng

App có 5 tab:

- **Quét** – quét mã vạch / mã QR (camera, VisionKit), tra cứu dinh dưỡng miễn phí từ [Open Food Facts](https://world.openfoodfacts.org); quét **nhãn dinh dưỡng** bằng OCR trên máy (tiếng Việt/Anh, đổi kJ → kcal); nhập tay khi cần.
- **Món ăn** – chụp ảnh món ăn bất kỳ, nhận diện trên máy (Vision) và ghép với bảng ~70 món phổ biến (món Việt, đồ ăn nhanh, đồ uống, trái cây) có calo ước tính; tìm món không cần dấu.
- **Tập luyện** – 30 môn với hệ số MET, ghi buổi tập và tính calo đốt; lịch tập gợi ý theo mục tiêu (tự chọn môn ít tác động khớp cho người ≥ 60 tuổi hoặc BMI béo phì); bài tập tại nhà không dụng cụ.
- **Cơ thể** – BMI (chuẩn châu Á), cân nặng hợp lý, BMR/TDEE (Mifflin-St Jeor), calo mục tiêu giảm/giữ/tăng cân, đạm–béo–tinh bột, nước, % mỡ ước tính, eo/chiều cao; gợi ý thực phẩm nên ăn/hạn chế.
  - **Kiểm tra triệu chứng** – đánh giá mức độ cần đi khám (cấp cứu 115 / trong ngày / vài ngày / tự chăm sóc), nguyên nhân thường gặp, chuyên khoa, chăm sóc – ăn uống, nhóm thuốc không kê đơn (không ghi liều), mẹo dân gian kèm cảnh báo. Đây là công cụ tham khảo, **không phải chẩn đoán y khoa**.
- **Nhật ký** – calo ăn vào, đốt khi tập và còn lại theo ngày (lưu trên máy bằng SwiftData).

Yêu cầu: iOS 17 trở lên. Quét bằng camera cần iPhone thật; trên simulator app hiện nút mã mẫu để thử.

## Kiểm tra app khi không có máy Mac

Mỗi lần đẩy code lên GitHub, workflow **iOS build & test** (`.github/workflows/ios.yml`) chạy trên máy macOS của GitHub:

1. Build app và chạy unit test.
2. Mở app trong iPhone simulator và chụp màn hình các trang chính.
3. Đóng gói bản build cho simulator.

Xem kết quả: tab **Actions** của repo → chọn lần chạy mới nhất → phần **Artifacts**:

- `screenshots` – ảnh chụp màn hình app.
- `CalorieScan-simulator-app` – file `CalorieScan-simulator.zip`. Tải lên [appetize.io](https://appetize.io/upload) để dùng thử app trên iPhone ảo ngay trong trình duyệt.

## Cấu trúc

```
project.yml              # cấu hình project cho XcodeGen (tạo CalorieScan.xcodeproj)
CalorieScan/
  App/                   # điểm khởi động, TabView, chế độ demo cho ảnh chụp
  Models/                # sản phẩm, món ăn, bài tập, triệu chứng, nhật ký (SwiftData)
  Services/              # Open Food Facts, OCR nhãn, nhận diện món, tính toán cơ thể, đánh giá triệu chứng
  Views/                 # các màn hình SwiftUI
CalorieScanTests/        # unit test
```

## Build trên máy Mac (nếu có)

```bash
brew install xcodegen
xcodegen generate
open CalorieScan.xcodeproj
```
