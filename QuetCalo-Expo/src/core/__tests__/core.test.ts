/// <reference types="node" />
import assert from "node:assert/strict";
import { test } from "node:test";
import { classifyScan, effectiveKcalPerServing, kcalText, shortText, Calorie } from "../basics";
import { offUrl, parseOFF, lookupProduct } from "../openFoodFacts";
import { parseLabel } from "../labelParser";
import { FOODS, foodById, foodProduct, kcalPerPortion, matchFoods, searchFoods } from "../foods";
import { bmiCategory, bodyReport, BodyProfile, EAT_MORE, LIMIT, nutritionAdvice } from "../health";
import { assess, CONDITIONS, emptySymptomInput, matchConditions, SYMPTOMS, SymptomInput } from "../symptoms";
import { EXERCISES, HOME_MOVES, exerciseById, exerciseKcal, searchExercises, workoutPlan, weeklyMinutes, isRest } from "../exercise";

const near = (a: number | undefined, b: number, eps = 0.01) => assert.ok(a !== undefined && Math.abs(a - b) <= eps, `${a} ≈ ${b}`);

test("Open Food Facts: calo, macro, chuỗi số, kJ, tên tiếng Việt, không tìm thấy", () => {
  const p = parseOFF({ status: 1, product: { product_name: "Nutella", brands: "Ferrero, Nutella", quantity: "400 g",
    serving_size: "15 g", serving_quantity: "15", nutriments: { "energy-kcal_100g": 539, "energy-kcal_serving": 80.9,
    proteins_100g: 6.3, fat_100g: 30.9, note: "abc", flag: true } } }, "3017624010701")!;
  assert.equal(p.name, "Nutella"); assert.equal(p.brand, "Ferrero"); assert.equal(p.kcalPer100g, 539);
  assert.equal(p.servingGrams, 15); near(p.kcalPerServing, 80.9); assert.equal(p.source, "openFoodFacts");
  near(parseOFF({ status: 1, product: { product_name: "T", nutriments: { energy_100g: "2092" } } }, "12345678")!.kcalPer100g, 500, 0.1);
  assert.equal(parseOFF({ status: 1, product: { product_name: "Fresh", product_name_vi: "Sữa tươi", nutriments: {} } }, "1")!.name, "Sữa tươi");
  assert.equal(parseOFF({ status: 1, product: { product_name: "  ", nutriments: {} } }, "12345678")!.name, "Sản phẩm 12345678");
  assert.equal(parseOFF({ status: 0, status_verbose: "product not found" }, "0"), undefined);
  assert.equal(offUrl("abc"), undefined);
  assert.ok(offUrl("3017624010701")!.startsWith("https://world.openfoodfacts.org/api/v2/product/3017624010701.json"));
});

test("lookupProduct: 404 → undefined, lỗi máy chủ → ném lỗi", async () => {
  const fake = (status: number, body: unknown = {}) => (async () => ({ status, ok: status < 300, json: async () => body })) as unknown as typeof fetch;
  assert.equal(await lookupProduct("3017624010701", fake(404)), undefined);
  await assert.rejects(lookupProduct("3017624010701", fake(500)));
  assert.equal((await lookupProduct("3017624010701", fake(200, { status: 1, product: { product_name: "X", nutriments: {} } })))!.name, "X");
});

test("Đọc nhãn dinh dưỡng", () => {
  const vi = parseLabel(["THÔNG TIN DINH DƯỠNG", "Giá trị dinh dưỡng trong 100 g", "Năng lượng 2008 kJ / 480 kcal"]);
  assert.equal(vi.kcal, 480); assert.equal(vi.basis, "per100g");
  assert.equal(parseLabel(["Energy (kcal) 250", "per 100ml"]).kcal, 250);
  const us = parseLabel(["Nutrition Facts", "Serving size 2/3 cup (55g)", "Calories 230", "2,000 calories a day is used"]);
  assert.equal(us.kcal, 230); assert.equal(us.basis, "perServing"); assert.equal(us.servingGrams, 55);
  assert.equal(parseLabel(["Năng lượng: 52,5 kcal/100ml"]).kcal, 52.5);
  near(parseLabel(["Energy 1000 kJ per 100 g"]).kcal, 239, 0.1);
  const two = parseLabel(["Trong 100 g | Khẩu phần 30 g", "Năng lượng 539 kcal 162 kcal"]);
  assert.equal(two.kcal, 539); assert.deepEqual(two.allKcalValues, [539, 162]); assert.equal(two.servingGrams, 30);
  assert.equal(parseLabel(["Hello", "Thành phần: bột mì, đường"]).kcal, undefined);
});

test("Mã vạch / QR", () => {
  assert.deepEqual(classifyScan("3017624010701"), { kind: "barcode", code: "3017624010701" });
  assert.deepEqual(classifyScan(" 5449000000996\n"), { kind: "barcode", code: "5449000000996" });
  assert.deepEqual(classifyScan("https://world.openfoodfacts.org/product/3017624010701/nutella"), { kind: "barcode", code: "3017624010701" });
  assert.deepEqual(classifyScan("https://id.gs1.org/01/09506000134352"), { kind: "barcode", code: "9506000134352" });
  assert.deepEqual(classifyScan("https://example.com"), { kind: "text", text: "https://example.com" });
  assert.deepEqual(classifyScan("12345"), { kind: "text", text: "12345" });
});

test("Tính calo và định dạng", () => {
  near(Calorie.per100g(480, 30), 144); assert.equal(Calorie.per100g(480, -5), 0); near(Calorie.perServing(80, 2.5), 200);
  near(effectiveKcalPerServing({ name: "X", servingGrams: 30, kcalPer100g: 480, source: "manual" }), 144);
  assert.equal(kcalText(143.6), "144 kcal"); assert.equal(shortText(6.2), "6,2"); assert.equal(shortText(30), "30"); assert.equal(shortText(2.17), "2,2");
});

test("Bảng món ăn, ghép nhãn ảnh, tìm kiếm", () => {
  assert.equal(FOODS.length, 68); assert.equal(new Set(FOODS.map((f) => f.id)).size, 68);
  for (const f of FOODS) assert.ok(f.kcalPer100g >= 10 && f.kcalPer100g <= 950 && f.portionGrams > 0 && f.visionLabels.length, f.id);
  const g = matchFoods([{ text: "banana", confidence: 0.9 }, { text: "fruit", confidence: 0.5 }, { text: "ramen", confidence: 0.3 }]);
  assert.equal(g[0].food.id, "chuoi"); assert.ok(g.some((x) => x.food.id === "pho-bo")); assert.ok(g.length <= 6);
  assert.equal(matchFoods([{ text: "Fried_Chicken", confidence: 0.8 }])[0].food.id, "ga-ran");
  assert.ok(matchFoods([{ text: "Bananas", confidence: 0.8 }]).some((x) => x.food.id === "chuoi"));
  assert.equal(matchFoods([{ text: "car", confidence: 0.9 }]).length, 0);
  assert.ok(searchFoods("pho").some((f) => f.id === "pho-bo")); assert.ok(searchFoods("Cơm Tấm").some((f) => f.id === "com-tam"));
  assert.ok(searchFoods("dua hau").some((f) => f.id === "dua-hau")); assert.equal(searchFoods("").length, 68);
  const pho = foodById("pho-bo")!;
  near(kcalPerPortion(pho), 450); near(effectiveKcalPerServing(foodProduct(pho)), 450);
});

const profile = (o: Partial<BodyProfile>): BodyProfile => ({ sex: "male", age: 30, heightCm: 170, weightKg: 70, activity: "sedentary", goal: "maintain", ...o });

test("Chỉ số cơ thể", () => {
  assert.equal(bmiCategory(18.49), "underweight"); assert.equal(bmiCategory(18.5), "normal"); assert.equal(bmiCategory(23), "overweight");
  assert.equal(bmiCategory(25), "obese1"); assert.equal(bmiCategory(30), "obese2");
  const r = bodyReport(profile({ sex: "female", age: 28, heightCm: 158, weightKg: 62, activity: "light", goal: "lose" }))!;
  near(r.bmi, 24.84); assert.equal(r.category, "overweight"); near(r.bmr, 1306.5); near(r.tdee, 1796.44); assert.equal(r.targetKcal, 1300);
  near(r.healthyMin, 46.18); near(r.healthyMax, 57.17); near(r.weightChange, -4.83); near(r.proteinGrams, 99.2); near(r.waterLiters, 2.17);
  const m = bodyReport(profile({ heightCm: 175, activity: "moderate" }))!;
  near(m.bmr, 1648.75); assert.equal(m.targetKcal, 2560); near(m.proteinGrams * 4 + m.fatGrams * 9 + m.carbGrams * 4, m.targetKcal, 0.5);
  assert.equal(bodyReport(profile({ sex: "female", age: 60, heightCm: 150, weightKg: 45, goal: "lose" }))!.targetKcal, 1110);
  const kid = bodyReport(profile({ age: 15, heightCm: 160, weightKg: 50, waistCm: 85 }))!;
  near(kid.waistToHeight, 0.53); assert.equal(kid.isAdult, false); assert.equal(kid.bodyFatPercent, undefined);
  assert.equal(bodyReport(profile({ heightCm: 0 })), undefined);
  for (const list of [...Object.values(EAT_MORE), ...Object.values(LIMIT)]) for (const [id] of list) assert.ok(foodById(id), id);
  const p = profile({ sex: "female", age: 25, heightCm: 165, weightKg: 45, activity: "light", goal: "lose" });
  assert.ok(nutritionAdvice(p, bodyReport(p)!).tips.some((t) => t.includes("không nên giảm cân")));
});

const input = (o: Partial<SymptomInput>): SymptomInput => ({ ...emptySymptomInput(), ...o });

test("Kiểm tra triệu chứng", () => {
  const e = assess(input({ symptoms: ["headache"], redFlags: ["strokeSigns"] }));
  assert.equal(e.level, "emergency"); assert.ok(e.reasons[0].includes("dấu hiệu nguy hiểm"));
  assert.equal(assess(input({ symptoms: ["chestPain"] })).level, "urgent");
  const cold = assess(input({ symptoms: ["runnyNose", "soreThroat", "cough"] }));
  assert.equal(cold.level, "selfCare"); assert.equal(cold.matches[0].condition.id, "common-cold");
  // Cúm đứng đầu, sốt xuất huyết đứng sau: vẫn phải khuyên đi khám
  const flu = assess(input({ symptoms: ["fever", "headache", "muscleAche", "fatigue"], severity: "moderate" }));
  assert.notEqual(flu.matches[0].condition.id, "dengue"); assert.ok(flu.matches.some((m) => m.condition.id === "dengue"));
  assert.equal(flu.level, "seeDoctor"); assert.ok(flu.reasons.some((r) => r.includes("Sốt xuất huyết")));
  assert.equal(assess(input({ symptoms: ["fever"], duration: "fourToSevenDays" })).level, "urgent");
  const child = assess(input({ symptoms: ["diarrhea"], group: "childUnder5" }));
  assert.equal(child.level, "urgent"); assert.equal(child.showMedicationAdvice, false);
  assert.equal(assess(input({ symptoms: ["abdominalPain"], group: "pregnant" })).level, "urgent");
  const uti = assess(input({ symptoms: ["painfulUrination"] }));
  assert.equal(uti.matches[0].condition.id, "uti"); assert.equal(uti.level, "seeDoctor");
  assert.ok(!matchConditions(["backPain", "fever"]).some((m) => m.condition.id === "uti"));
  assert.equal(CONDITIONS.length, 16);
  for (const c of CONDITIONS) {
    assert.ok(c.required.every((s) => c.symptoms.includes(s)) && c.selfCare.length && c.seeDoctorIf.length, c.id);
    for (const id of [...c.eatFoodIDs, ...c.avoidFoodIDs]) assert.ok(foodById(id), `${c.id}: ${id}`);
  }
  assert.deepEqual(new Set(CONDITIONS.flatMap((c) => c.symptoms)), new Set(SYMPTOMS.map(([s]) => s)));
  assert.ok(CONDITIONS.find((c) => c.id === "dengue")!.otcMedicines.some((m) => m.includes("ibuprofen") && m.includes("KHÔNG")));
});

test("Tập luyện", () => {
  near(exerciseKcal(exerciseById("walk-brisk")!.met, 62, 30), 139.97); near(exerciseKcal(8, 70, 60), 588); assert.equal(exerciseKcal(8, 70, -10), 0);
  assert.equal(EXERCISES.length, 30); assert.equal(HOME_MOVES.length, 8); assert.equal(new Set(EXERCISES.map((e) => e.id)).size, 30);
  assert.ok(searchExercises("boi").some((e) => e.id === "swim-easy")); assert.ok(searchExercises("Cầu lông").some((e) => e.id === "badminton"));
  for (const goal of ["lose", "maintain", "gain"] as const) {
    for (const cat of ["normal", "obese2"] as const) {
      const plan = workoutPlan(goal, 30, cat);
      assert.equal(plan.days.length, 7); assert.ok(plan.days.some(isRest));
      for (const d of plan.days) for (const id of d.exerciseIDs) assert.ok(exerciseById(id), id);
    }
    const low = workoutPlan(goal, 65, "normal");
    assert.ok(low.lowImpact && !low.days.flatMap((d) => d.exerciseIDs).some((id) => exerciseById(id)!.highImpact));
  }
  assert.ok(weeklyMinutes(workoutPlan("lose", 30, "overweight")) >= 150);
});
