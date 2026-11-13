# Quét Calo (CalorieScan)

Ứng dụng iOS (SwiftUI) quét mã vạch / mã QR / nhãn dinh dưỡng trên bao bì sản phẩm và tính lượng calo.

## Tính năng

- **Quét mã vạch & mã QR** (EAN-13, EAN-8, UPC-E, Code 128, ITF-14, QR) bằng camera (VisionKit).
- **Tra cứu dinh dưỡng** miễn phí từ [Open Food Facts](https://world.openfoodfacts.org): kcal/100 g, kcal/khẩu phần, đạm, carb, đường, béo.
- **Quét nhãn dinh dưỡng** (OCR trên máy bằng Vision) cho sản phẩm chưa có trong cơ sở dữ liệu – tự tìm số kcal, đọc được nhãn tiếng Việt và tiếng Anh, đổi kJ → kcal.
- **Tính calo** theo số gram/ml hoặc số khẩu phần đã ăn.
- **Nhật ký calo** theo ngày, mục tiêu calo hằng ngày (lưu trên máy bằng SwiftData).
- Nhập mã vạch / calo thủ công khi cần.

Yêu cầu: iOS 17 trở lên. Quét bằng camera cần iPhone thật (iPhone XS trở lên); trên simulator app hiện nút mã mẫu để thử.

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
  Models/                # ProductInfo, FoodEntry (SwiftData), ScanPayload
  Services/              # Open Food Facts, đọc nhãn (OCR + parser), tính calo
  Views/                 # các màn hình SwiftUI
CalorieScanTests/        # unit test
```

## Build trên máy Mac (nếu có)

```bash
brew install xcodegen
xcodegen generate
open CalorieScan.xcodeproj
```
