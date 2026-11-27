#!/usr/bin/env bash
# Cài APK bản Expo lên emulator, mở từng màn hình qua deep link (quetcalo://),
# chụp màn hình, kiểm tra app không crash và module ML Kit đã được link.
set -u
APK="$1"
PKG=com.herisoft.quetcalo
OUT=expo-android-screenshots
mkdir -p "$OUT"

adb install -r "$APK"
adb shell pm grant "$PKG" android.permission.CAMERA || true
adb logcat -c || true

failed=0
adb shell am start -W -n "$PKG/.MainActivity"
sleep 25   # lần mở đầu: nạp JS bundle

shot() { # $1 tên ảnh, $2 đường dẫn deep link
  if [ -n "$2" ]; then adb shell am start -W -a android.intent.action.VIEW -d "quetcalo://$2" "$PKG" > /dev/null; fi
  sleep 8
  adb exec-out screencap -p > "$OUT/$1.png"
  adb exec-out uiautomator dump /dev/tty > "$OUT/$1.xml" 2>/dev/null || true
  if adb shell pidof "$PKG" > /dev/null; then echo "OK: $1"; else echo "::error::App không chạy sau khi mở '$1' (crash?)"; failed=1; fi
}

shot 1-quet ""
shot 2-mon-an "food"
shot 3-pho-bo "product?food=pho-bo"
shot 4-tap-luyen "exercise"
shot 5-co-the "body"
shot 6-trieu-chung "symptoms"
shot 7-nhat-ky "log"

# Module native ML Kit phải có: tab Món ăn hiện nút "Chọn ảnh" thay vì câu hướng dẫn nhập tay
if grep -q "Chọn ảnh" "$OUT/2-mon-an.xml"; then echo "OK: ML Kit image labeling đã link"
else echo "::error::Không thấy nút 'Chọn ảnh' ở tab Món ăn: module ML Kit chưa được link"; failed=1; fi
if grep -q "450 kcal" "$OUT/3-pho-bo.xml"; then echo "OK: Phở bò 450 kcal"
else echo "::error::Màn hình Phở bò không hiện 450 kcal"; failed=1; fi

adb logcat -d > "$OUT/logcat.txt" || true
if grep -qE "FATAL EXCEPTION|ReactNativeJS.*(Error|Exception)" "$OUT/logcat.txt"; then
  echo "::error::Có lỗi trong logcat:"
  grep -E -A 20 "FATAL EXCEPTION|ReactNativeJS.*(Error|Exception)" "$OUT/logcat.txt" | head -80
  failed=1
fi
ls -la "$OUT"
exit $failed
