// Sinh bởi App Builder AI
import { brand } from "./brand";

const strings = {
  "vi": {
    "loading": "Đang tải…",
    "errorTitle": "Đã có lỗi",
    "retry": "Thử lại",
    "cancel": "Hủy",
    "ok": "Đồng ý",
    "save": "Lưu",
    "delete": "Xóa",
    "settings": "Cài đặt",
    "appearance": "Giao diện",
    "themeSystem": "Theo hệ thống",
    "themeLight": "Sáng",
    "themeDark": "Tối",
    "about": "Thông tin",
    "version": "Phiên bản {version}",
    "notFound": "Không tìm thấy trang",
    "goHome": "Về trang chủ",
    "homeTitle": "Trang chủ",
    "welcome": "Chào mừng!",
    "welcomeMessage": "Đây là khung ứng dụng ban đầu. Mô tả tính năng trong App Builder AI để AI bổ sung màn hình và chức năng.",
    "openSettings": "Mở cài đặt"
  },
  "en": {
    "loading": "Loading…",
    "errorTitle": "Something went wrong",
    "retry": "Retry",
    "cancel": "Cancel",
    "ok": "OK",
    "save": "Save",
    "delete": "Delete",
    "settings": "Settings",
    "appearance": "Appearance",
    "themeSystem": "System",
    "themeLight": "Light",
    "themeDark": "Dark",
    "about": "About",
    "version": "Version {version}",
    "notFound": "Page not found",
    "goHome": "Go home",
    "homeTitle": "Home",
    "welcome": "Welcome!",
    "welcomeMessage": "This is the starter shell. Describe features in App Builder AI and the AI will add screens and functionality.",
    "openSettings": "Open settings"
  }
} as const;

export type StringKey = keyof (typeof strings)["vi"];

export function t(key: StringKey, vars?: Record<string, string | number>): string {
  const table = strings[brand.language] ?? strings.vi;
  let s: string = table[key] ?? strings.vi[key] ?? key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
  return s;
}
