import { Calorie, searchKey } from "./basics";

export type LabelBasis = "per100g" | "perServing";
export interface LabelResult {
  kcal?: number;
  basis: LabelBasis;
  servingGrams?: number;
  allKcalValues: number[];
}

const NUMBER = String.raw`(\d+(?:\.\d+)?)`;

function values(pattern: string, text: string): number[] {
  const re = new RegExp(pattern, "g");
  const out: number[] = [];
  for (const m of text.matchAll(re)) {
    const v = Number(m[1]);
    if (Number.isFinite(v)) out.push(v);
  }
  return out;
}

/** Chữ thường, bỏ dấu, đổi dấu phẩy thập phân thành dấu chấm. */
export function normalizeLabel(text: string): string {
  return searchKey(text).replace(/(\d),(\d)/g, "$1.$2");
}

/** Tìm số calo trong văn bản OCR của nhãn dinh dưỡng (tiếng Việt hoặc tiếng Anh). */
export function parseLabel(lines: string[]): LabelResult {
  const text = normalizeLabel(lines.join(" \n "));
  const before = values(NUMBER + String.raw`\s*k\s?ca[l1i]`, text);
  const after = values(String.raw`kca[l1i]\)?\s*[:\-/]?\s*` + NUMBER, text);
  const calories = values(String.raw`calo(?:ries?)?\s*[:\-]?\s*` + NUMBER, text);
  const kj = values(NUMBER + String.raw`\s*kj`, text).map(Calorie.kJToKcal);
  const ok = (v: number) => v > 0 && v <= 2000;
  const kcal = [before, after, calories, kj].map((l) => l.filter(ok)).find((l) => l.length > 0)?.[0];
  const mentions100 = values(String.raw`(100)\s?(?:g|ml)\b`, text).length > 0;
  const mentionsServing = /serving|khau phan|phan an|moi phan|1 phan|per pack|portion/.test(text);
  const servingGrams = values(
    String.raw`(?:serving size|per serving|khau phan|phan an|moi phan|1 phan|portion)[\s\S]{0,40}?` + NUMBER + String.raw`\s*(?:g|ml)\b`,
    text,
  ).find((v) => v > 0 && v < 2000);
  return { kcal, basis: !mentions100 && mentionsServing ? "perServing" : "per100g", servingGrams, allKcalValues: before.filter(ok) };
}
