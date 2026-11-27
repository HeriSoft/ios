/** Hàm dùng chung: làm tròn, định dạng số kiểu Việt Nam, khóa tìm kiếm không dấu, tính calo. */

export function roundHalfUp(x: number): number {
  return x >= 0 ? Math.floor(x + 0.5) : -Math.floor(-x + 0.5);
}

/** "144 kcal" */
export function kcalText(x: number): string {
  return `${roundHalfUp(x)} kcal`;
}

/** Tối đa 1 chữ số thập phân, dấu phẩy: 6,2 · 30 */
export function shortText(x: number): string {
  const r = roundHalfUp(x * 10) / 10;
  return Number.isInteger(r) ? String(r) : r.toFixed(1).replace(".", ",");
}

/** Chữ thường, bỏ dấu tiếng Việt (kể cả đ) để tìm kiếm. */
export function searchKey(text: string): string {
  return text
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .normalize("NFD")
    .replace(/\p{M}+/gu, "")
    .toLowerCase()
    .trim();
}

export const Calorie = {
  per100g: (per100g: number, amount: number) => Math.max(0, (per100g * amount) / 100),
  perServing: (perServing: number, servings: number) => Math.max(0, perServing * servings),
  kJToKcal: (kj: number) => kj / 4.184,
};

export type ProductSource = "openFoodFacts" | "label" | "manual" | "estimate";

/** Thông tin dinh dưỡng của một sản phẩm (Open Food Facts, nhãn, tự nhập hoặc bảng món ăn). */
export interface ProductInfo {
  barcode?: string;
  name: string;
  brand?: string;
  imageUrl?: string;
  quantityText?: string;
  servingSizeText?: string;
  servingGrams?: number;
  kcalPer100g?: number;
  kcalPerServing?: number;
  protein100g?: number;
  carbs100g?: number;
  sugars100g?: number;
  fat100g?: number;
  source: ProductSource;
}

export function effectiveKcalPerServing(p: ProductInfo): number | undefined {
  if (p.kcalPerServing != null) return p.kcalPerServing;
  if (p.kcalPer100g != null && p.servingGrams && p.servingGrams > 0) return Calorie.per100g(p.kcalPer100g, p.servingGrams);
  return undefined;
}

export type ScanPayload = { kind: "barcode"; code: string } | { kind: "text"; text: string };

export const isBarcode = (v: string) => v.length >= 8 && v.length <= 14 && /^[0-9]+$/.test(v);
/** GTIN-14 bắt đầu bằng 0 tương đương EAN-13. */
const normalizeCode = (c: string) => (c.length === 14 && c.startsWith("0") ? c.slice(1) : c);

/** Phân loại nội dung đọc được từ mã vạch / mã QR. */
export function classifyScan(raw: string): ScanPayload {
  const trimmed = raw.trim();
  if (isBarcode(trimmed)) return { kind: "barcode", code: normalizeCode(trimmed) };
  let url: URL | undefined;
  try {
    url = new URL(trimmed);
  } catch {
    url = undefined;
  }
  if (url && url.protocol.startsWith("http")) {
    const parts = url.pathname.split("/").filter(Boolean).reverse();
    const fromPath = parts.find(isBarcode);
    if (fromPath) return { kind: "barcode", code: normalizeCode(fromPath) };
    for (const v of url.searchParams.values()) if (isBarcode(v)) return { kind: "barcode", code: normalizeCode(v) };
  }
  return { kind: "text", text: trimmed };
}
