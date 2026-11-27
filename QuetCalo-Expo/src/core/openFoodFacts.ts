import { Calorie, ProductInfo } from "./basics";

export const OFF_FIELDS = [
  "code", "product_name", "product_name_vi", "product_name_en", "brands", "image_front_small_url",
  "image_front_url", "quantity", "serving_size", "serving_quantity", "nutriments",
];

export function offUrl(barcode: string): string | undefined {
  if (!/^[0-9]{6,14}$/.test(barcode)) return undefined;
  return `https://world.openfoodfacts.org/api/v2/product/${barcode}.json?fields=${OFF_FIELDS.join(",")}`;
}

/** Số có thể là number hoặc chuỗi ("15", "2,5"). */
function lossy(v: unknown): number | undefined {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v.trim().replace(",", "."));
    return v.trim() !== "" && Number.isFinite(n) ? n : undefined;
  }
  return undefined;
}

function str(o: Record<string, unknown>, k: string): string | undefined {
  const v = o[k];
  return typeof v === "string" && v.trim() ? v.trim() : undefined;
}

/** Đọc JSON của Open Food Facts. Trả về undefined khi không tìm thấy. */
export function parseOFF(json: unknown, barcode: string): ProductInfo | undefined {
  const root = (json ?? {}) as Record<string, unknown>;
  if ("status" in root && lossy(root.status) === 0) return undefined;
  const p = root.product as Record<string, unknown> | undefined;
  if (!p || typeof p !== "object") return undefined;
  const n: Record<string, number> = {};
  const rawN = (p.nutriments ?? {}) as Record<string, unknown>;
  for (const [k, v] of Object.entries(rawN)) {
    const num = lossy(v);
    if (num !== undefined) n[k] = num;
  }
  const kj = (k: string) => (n[k] !== undefined ? Calorie.kJToKcal(n[k]) : undefined);
  const serving = lossy(p.serving_quantity);
  return {
    barcode,
    name: str(p, "product_name_vi") ?? str(p, "product_name") ?? str(p, "product_name_en") ?? `Sản phẩm ${barcode}`,
    brand: str(p, "brands")?.split(",")[0]?.trim(),
    imageUrl: str(p, "image_front_small_url") ?? str(p, "image_front_url"),
    quantityText: str(p, "quantity"),
    servingSizeText: str(p, "serving_size"),
    servingGrams: serving && serving > 0 ? serving : undefined,
    kcalPer100g: n["energy-kcal_100g"] ?? kj("energy-kj_100g") ?? kj("energy_100g"),
    kcalPerServing: n["energy-kcal_serving"] ?? kj("energy-kj_serving") ?? kj("energy_serving"),
    protein100g: n["proteins_100g"],
    carbs100g: n["carbohydrates_100g"],
    sugars100g: n["sugars_100g"],
    fat100g: n["fat_100g"],
    source: "openFoodFacts",
  };
}

export class LookupError extends Error {}

/** Tra cứu sản phẩm qua mạng. undefined = không có trong cơ sở dữ liệu. */
export async function lookupProduct(barcode: string, fetchFn: typeof fetch = fetch): Promise<ProductInfo | undefined> {
  const url = offUrl(barcode);
  if (!url) throw new LookupError("Mã vạch không hợp lệ.");
  const res = await fetchFn(url, { headers: { "User-Agent": "QuetCalo-Expo/1.0" } });
  if (res.status === 404) return undefined;
  if (!res.ok) throw new LookupError(`Máy chủ trả về lỗi (${res.status}). Vui lòng thử lại.`);
  return parseOFF(await res.json(), barcode);
}
