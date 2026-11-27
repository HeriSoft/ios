# Quét Calo (bản Expo / React Native)

Quét mã vạch/QR và nhãn dinh dưỡng trên bao bì, ước tính calo món ăn, ghi buổi tập, tính BMI/BMR/TDEE và kiểm tra triệu chứng.
Đây là bản React Native/Expo của app Quét Calo, cùng tính năng và dữ liệu với bản iOS (`CalorieScan/`, SwiftUI) và Android (`android/`, Kotlin). Bản này dựng theo cấu trúc dự án của **App Builder AI** nên mở và chỉnh được trong App Builder.

Expo SDK 58 · Expo Router · TypeScript · AsyncStorage.

## Mở trong App Builder

1. Kéo repo mới nhất về (`git pull`).
2. Trong App Builder: **Mở thư mục…** → chọn thư mục `QuetCalo-Expo` (không chọn thư mục gốc repo).
3. App Builder đọc `.appbuilder/project.json` (tên, màu, danh sách màn hình, tiêu chí nghiệm thu).
4. Bấm cài đặt phụ thuộc (`npm install`), rồi chạy web hoặc Android.

## Màn hình

| Tab / route | Nội dung |
|---|---|
| `/(tabs)/index` Quét | Camera quét mã vạch/QR (native), nhập mã tay, mã mẫu, nút quét nhãn |
| `/(tabs)/food` Món ăn | Chụp món ăn để nhận diện (native), tìm 68 món phổ biến |
| `/(tabs)/exercise` Tập luyện | Calo đốt hôm nay, ghi buổi tập (30 môn, công thức MET) |
| `/(tabs)/body` Cơ thể | BMI (ngưỡng châu Á), BMR/TDEE, calo mục tiêu, nên ăn/hạn chế |
| `/(tabs)/log` Nhật ký | Calo còn lại, mục tiêu, lịch sử theo ngày |
| `/product`, `/lookup/[code]` | Chi tiết sản phẩm (Open Food Facts), chọn gram/khẩu phần |
| `/label`, `/manual`, `/qr-text` | Đọc nhãn dinh dưỡng (OCR), nhập tay, nội dung QR |
| `/plan`, `/home-workout`, `/move/[id]` | Lịch tập gợi ý, 8 bài tập tại nhà |
| `/symptoms`, `/symptom-result`, `/condition/[id]` | Kiểm tra triệu chứng, mức độ cần đi khám, cách chăm sóc |

Ảnh chụp bản web: `docs/screenshots/`.

## Chạy thử

```powershell
npm install
npx expo start --web      # chạy trên trình duyệt
npm test                  # kiểm thử logic (calo, nhãn, BMI, triệu chứng, bài tập)
npm run typecheck
```

## Tính năng cần bản build native

| Tính năng | Web | Expo Go | Build native (APK/IPA) |
|---|---|---|---|
| Tra mã vạch, món ăn, tập luyện, cơ thể, triệu chứng, nhật ký | ✅ | ✅ | ✅ |
| Camera quét mã vạch/QR | — (nhập tay) | ✅ | ✅ |
| Đọc chữ trên nhãn (OCR, ML Kit) | — (nhập tay) | — | ✅ |
| Nhận diện món ăn từ ảnh (ML Kit) | — (tìm theo tên) | — | ✅ |

OCR và nhận diện ảnh dùng `@react-native-ml-kit/*`, cần build native: `npx expo prebuild` rồi `npx expo run:android`, hoặc build bằng EAS. Khi không có module native, app tự ẩn nút chụp và hướng dẫn nhập tay.

## Dữ liệu và quyền riêng tư

- Nhật ký, hồ sơ cơ thể lưu local bằng AsyncStorage (`quetcalo.v1`). App không chứa API key/secret.
- Tra mã vạch gọi Open Food Facts (miễn phí, cộng đồng đóng góp), cần mạng.
- Kiểm tra triệu chứng chỉ mang tính tham khảo, không thay thế bác sĩ. Có dấu hiệu nguy hiểm → gọi 115.
