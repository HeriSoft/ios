#!/usr/bin/env bash
# Cài APK lên emulator, mở từng màn hình demo, chụp màn hình và kiểm tra app không bị crash.
set -u
APK="$1"
PKG=com.herisoft.caloriescan
OUT=android-screenshots
mkdir -p "$OUT"

adb install -r "$APK"
adb shell pm grant "$PKG" android.permission.CAMERA || true
adb logcat -c || true

failed=0
for screen in scan detail label food exercise plan body symptoms log; do
  adb shell am force-stop "$PKG"
  adb shell am start -W -n "$PKG/.MainActivity" --es demoScreen "$screen"
  sleep 6
  adb exec-out screencap -p > "$OUT/$screen.png"
  if adb shell pidof "$PKG" > /dev/null; then
    echo "OK: $screen"
  else
    echo "::error::App is not running after opening '$screen' (crash?)"
    failed=1
  fi
done

adb logcat -d > "$OUT/logcat.txt" || true
if grep -q "FATAL EXCEPTION" "$OUT/logcat.txt"; then
  echo "::error::Crash found in logcat:"
  grep -A 30 "FATAL EXCEPTION" "$OUT/logcat.txt" | head -80
  failed=1
fi
ls -la "$OUT"
exit $failed
