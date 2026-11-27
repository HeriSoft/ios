import { foodById, FoodItem } from "./foods";
import { roundHalfUp, shortText } from "./basics";

export type Sex = "male" | "female";
export const SEX_TITLE: Record<Sex, string> = { male: "Nam", female: "Nữ" };

export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "veryActive";
export const ACTIVITY: Record<ActivityLevel, { factor: number; title: string }> = {
  sedentary: { factor: 1.2, title: "Ít vận động (ngồi nhiều)" },
  light: { factor: 1.375, title: "Nhẹ (tập 1–3 buổi/tuần)" },
  moderate: { factor: 1.55, title: "Vừa (tập 3–5 buổi/tuần)" },
  active: { factor: 1.725, title: "Nhiều (tập 6–7 buổi/tuần)" },
  veryActive: { factor: 1.9, title: "Rất nhiều (lao động nặng)" },
};

export type WeightGoal = "lose" | "maintain" | "gain";
export const GOAL_TITLE: Record<WeightGoal, string> = { lose: "Giảm cân", maintain: "Giữ cân", gain: "Tăng cân" };

export interface BodyProfile {
  sex: Sex;
  age: number;
  heightCm: number;
  weightKg: number;
  activity: ActivityLevel;
  goal: WeightGoal;
  waistCm?: number;
}

export const isValidProfile = (p: BodyProfile) =>
  p.age >= 10 && p.age <= 100 && p.heightCm >= 100 && p.heightCm <= 250 && p.weightKg >= 20 && p.weightKg <= 300;

/** BMI cho người trưởng thành châu Á (Bộ Y tế Việt Nam áp dụng). */
export type BMICategory = "underweight" | "normal" | "overweight" | "obese1" | "obese2";
export const BMI_TITLE: Record<BMICategory, string> = {
  underweight: "Thiếu cân", normal: "Bình thường", overweight: "Thừa cân", obese1: "Béo phì độ I", obese2: "Béo phì độ II",
};
export function bmiCategory(bmi: number): BMICategory {
  if (bmi < 18.5) return "underweight";
  if (bmi < 23) return "normal";
  if (bmi < 25) return "overweight";
  if (bmi < 30) return "obese1";
  return "obese2";
}

export interface BodyReport {
  bmi: number;
  category: BMICategory;
  healthyMin: number;
  healthyMax: number;
  /** Dương = cần tăng, âm = cần giảm, 0 = đã hợp lý. */
  weightChange: number;
  bmr: number;
  tdee: number;
  targetKcal: number;
  proteinGrams: number;
  fatGrams: number;
  carbGrams: number;
  waterLiters: number;
  bodyFatPercent?: number;
  waistToHeight?: number;
  isAdult: boolean;
}

export const bmiOf = (weightKg: number, heightCm: number) => weightKg / (heightCm / 100) ** 2;
/** Mifflin-St Jeor */
export const bmrOf = (p: BodyProfile) => 10 * p.weightKg + 6.25 * p.heightCm - 5 * p.age + (p.sex === "male" ? 5 : -161);
export const minimumKcal = (sex: Sex) => (sex === "female" ? 1200 : 1500);

export function bodyReport(p: BodyProfile): BodyReport | undefined {
  if (!isValidProfile(p)) return undefined;
  const bmi = bmiOf(p.weightKg, p.heightCm);
  const m2 = (p.heightCm / 100) ** 2;
  const healthyMin = 18.5 * m2;
  const healthyMax = 22.9 * m2;
  const weightChange = p.weightKg < healthyMin ? healthyMin - p.weightKg : p.weightKg > healthyMax ? healthyMax - p.weightKg : 0;
  const bmr = bmrOf(p);
  const tdee = bmr * ACTIVITY[p.activity].factor;
  const target =
    p.goal === "lose" ? Math.min(tdee, Math.max(tdee - 500, minimumKcal(p.sex))) : p.goal === "gain" ? tdee + 300 : tdee;
  const targetKcal = roundHalfUp(target / 10) * 10;
  const proteinGrams = (p.goal === "maintain" ? 1.2 : 1.6) * p.weightKg;
  const fatGrams = (targetKcal * 0.27) / 9;
  const carbGrams = Math.max(0, (targetKcal - proteinGrams * 4 - fatGrams * 9) / 4);
  const isAdult = p.age >= 18;
  return {
    bmi, category: bmiCategory(bmi), healthyMin, healthyMax, weightChange, bmr, tdee, targetKcal,
    proteinGrams, fatGrams, carbGrams, waterLiters: p.weightKg * 0.035,
    bodyFatPercent: isAdult ? Math.max(3, 1.2 * bmi + 0.23 * p.age - 10.8 * (p.sex === "male" ? 1 : 0) - 5.4) : undefined,
    waistToHeight: p.waistCm && p.waistCm > 0 ? p.waistCm / p.heightCm : undefined,
    isAdult,
  };
}

export interface FoodSuggestion { food: FoodItem; reason: string }
export interface NutritionAdvice { eatMore: FoodSuggestion[]; limit: FoodSuggestion[]; tips: string[] }

export const EAT_MORE: Record<WeightGoal, [string, string][]> = {
  lose: [
    ["trung-luoc", "Nhiều đạm, ít calo, giúp no lâu"], ["canh-chua", "Nhiều nước và rau, rất ít calo"],
    ["rau-xao", "Chất xơ giúp no lâu, ít năng lượng"], ["goi-cuon", "Nhiều rau, ít dầu mỡ hơn món chiên"],
    ["pho-ga", "Đủ đạm; chọn tô nhỏ, ít bánh phở"], ["oi", "Nhiều chất xơ và vitamin C"],
    ["du-du", "Ít calo, tốt cho tiêu hóa"], ["dua-hau", "Rất ít calo, nhiều nước"],
  ],
  maintain: [
    ["ca-kho", "Cá cung cấp đạm và chất béo tốt"], ["rau-xao", "Rau xanh mỗi bữa cho đủ chất xơ"],
    ["trung-luoc", "Nguồn đạm rẻ và dễ chế biến"], ["com-trang", "Tinh bột vừa đủ: khoảng 1–2 chén mỗi bữa"],
    ["canh-chua", "Bổ sung rau và nước"], ["chuoi", "Kali và năng lượng cho buổi tập"],
    ["cam", "Vitamin C, ăn nguyên quả tốt hơn uống nước ép"],
  ],
  gain: [
    ["bo", "Chất béo tốt, nhiều năng lượng trong khẩu phần nhỏ"], ["sinh-to", "Dễ uống thêm calo giữa các bữa"],
    ["trung-chien", "Đạm và năng lượng để tăng cơ"], ["com-tam", "Nhiều năng lượng và đạm"],
    ["xoi", "Tinh bột đậm đặc cho bữa sáng"], ["chuoi", "Bữa phụ nhanh, nhiều năng lượng"],
    ["sua-tuoi", "Thêm đạm và calo, uống sau khi tập"], ["banh-mi-thit", "Bữa phụ tiện lợi, đủ đạm và tinh bột"],
  ],
};

export const LIMIT: Record<WeightGoal, [string, string][]> = {
  lose: [
    ["tra-sua", "Nhiều đường: 1 ly ≈ 1 bữa ăn"], ["nuoc-ngot", "Calo rỗng, không giúp no"], ["ga-ran", "Nhiều dầu mỡ"],
    ["khoai-tay-chien", "Nhiều dầu, dễ ăn quá nhiều"], ["banh-ngot", "Nhiều đường và chất béo"], ["cha-gio", "Chiên ngập dầu"],
  ],
  maintain: [
    ["nuoc-ngot", "Calo rỗng, dễ tăng cân khi uống thường xuyên"], ["tra-sua", "Nhiều đường"],
    ["ga-ran", "Nhiều dầu mỡ, nên ăn thỉnh thoảng"],
  ],
  gain: [
    ["nuoc-ngot", "Calo rỗng, không giúp tăng cơ"],
    ["khoai-tay-chien", "Nên tăng cân bằng thức ăn giàu đạm thay vì đồ chiên"],
  ],
};

export function nutritionAdvice(p: BodyProfile, r: BodyReport): NutritionAdvice {
  const pick = (list: [string, string][]) =>
    list.flatMap(([id, reason]) => {
      const food = foodById(id);
      return food ? [{ food, reason }] : [];
    });
  const tips: string[] = [];
  if (!r.isAdult) tips.push("Dưới 18 tuổi cần đánh giá theo biểu đồ tăng trưởng theo tuổi. Kết quả ở đây chỉ để tham khảo, hãy hỏi bác sĩ nhi khoa.");
  if (p.goal === "lose" && r.category === "underweight")
    tips.push('Bạn đang thiếu cân, không nên giảm cân thêm. Hãy cân nhắc mục tiêu "Giữ cân" hoặc "Tăng cân".');
  if (p.goal === "gain" && (r.category === "obese1" || r.category === "obese2"))
    tips.push("Chỉ số BMI đang ở mức béo phì, nên hỏi ý kiến bác sĩ trước khi tăng cân.");
  if (r.category === "obese1" || r.category === "obese2")
    tips.push("BMI ở mức béo phì làm tăng nguy cơ tiểu đường, huyết áp cao và tim mạch. Nên khám sức khỏe định kỳ.");
  if (r.category === "underweight")
    tips.push("Thiếu cân kéo dài có thể do ăn chưa đủ hoặc vấn đề sức khỏe khác. Nếu sụt cân không rõ lý do, hãy đi khám.");
  if ((r.waistToHeight ?? 0) > 0.5)
    tips.push("Vòng eo lớn hơn một nửa chiều cao: mỡ bụng nhiều, tăng nguy cơ bệnh chuyển hóa. Ưu tiên giảm vòng eo.");
  tips.push(
    p.goal === "lose"
      ? `Giảm khoảng 0,5 kg mỗi tuần là an toàn. Đừng ăn dưới ${minimumKcal(p.sex)} kcal/ngày nếu không có hướng dẫn của chuyên gia.`
      : p.goal === "gain"
        ? "Tăng cân kèm tập sức mạnh 2–3 buổi/tuần để tăng cơ thay vì tăng mỡ."
        : "Giữ cân bằng cách ăn đủ bữa, nhiều rau và theo dõi cân nặng mỗi tuần.",
  );
  tips.push(`Ăn khoảng ${roundHalfUp(r.proteinGrams)} g đạm mỗi ngày, chia đều các bữa (thịt, cá, trứng, đậu, sữa).`);
  tips.push(`Uống khoảng ${shortText(r.waterLiters)} lít nước mỗi ngày, nhiều hơn khi trời nóng hoặc tập luyện.`);
  return { eatMore: pick(EAT_MORE[p.goal]), limit: pick(LIMIT[p.goal]), tips };
}
