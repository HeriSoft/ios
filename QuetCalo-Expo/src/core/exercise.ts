import { BMICategory, WeightGoal } from "./health";
import { searchKey } from "./basics";

export type ExerciseCategory = "cardio" | "strength" | "sport" | "flexibility" | "daily";
export const CATEGORY_TITLE: Record<ExerciseCategory, string> = {
  cardio: "Cardio", strength: "Sức mạnh", sport: "Thể thao", flexibility: "Dẻo dai & thư giãn", daily: "Hoạt động hằng ngày",
};

/** Một môn tập với hệ số MET (theo Compendium of Physical Activities). */
export interface Exercise {
  id: string;
  name: string;
  aliases: string[];
  met: number;
  category: ExerciseCategory;
  /** Tên SF Symbols của bản iOS (bản Expo chọn icon theo nhóm). */
  icon: string;
  /** Có chạy nhảy, tác động mạnh lên khớp. */
  highImpact: boolean;
}

/** Calo đốt: MET × 3,5 × cân nặng (kg) / 200 × số phút. */
export const exerciseKcal = (met: number, weightKg: number, minutes: number) => Math.max(0, ((met * 3.5 * weightKg) / 200) * minutes);

export const EXERCISES: Exercise[] = [

        // Cardio
        {id: "walk-slow", name: "Đi bộ chậm", aliases: ["walking", "di bo"], met: 2.8, category: "cardio", icon: "figure.walk", highImpact: false},
        {id: "walk-brisk", name: "Đi bộ nhanh", aliases: ["brisk walking", "di bo nhanh"], met: 4.3, category: "cardio", icon: "figure.walk.motion", highImpact: false},
        {id: "jog", name: "Chạy bộ chậm (~8 km/h)", aliases: ["jogging", "chay bo"], met: 8.3, category: "cardio", icon: "figure.run", highImpact: true},
        {id: "run", name: "Chạy bộ (~10 km/h)", aliases: ["running", "chay"], met: 9.8, category: "cardio", icon: "figure.run", highImpact: true},
        {id: "cycle-easy", name: "Đạp xe nhẹ", aliases: ["cycling", "xe dap"], met: 4.0, category: "cardio", icon: "figure.outdoor.cycle", highImpact: false},
        {id: "cycle-moderate", name: "Đạp xe vừa (~20 km/h)", aliases: ["cycling", "xe dap"], met: 8.0, category: "cardio", icon: "figure.outdoor.cycle", highImpact: false},
        {id: "swim-easy", name: "Bơi nhẹ nhàng", aliases: ["swimming", "boi"], met: 6.0, category: "cardio", icon: "figure.pool.swim", highImpact: false},
        {id: "swim-fast", name: "Bơi nhanh", aliases: ["swimming", "boi"], met: 9.8, category: "cardio", icon: "figure.pool.swim", highImpact: false},
        {id: "jump-rope", name: "Nhảy dây", aliases: ["jump rope", "nhay day"], met: 11.8, category: "cardio", icon: "figure.jumprope", highImpact: true},
        {id: "stairs", name: "Leo cầu thang", aliases: ["stairs", "cau thang"], met: 8.0, category: "cardio", icon: "figure.stairs", highImpact: false},
        {id: "aerobic", name: "Aerobic / Zumba", aliases: ["aerobic", "zumba"], met: 7.3, category: "cardio", icon: "figure.dance", highImpact: true},
        {id: "elliptical", name: "Máy tập elip", aliases: ["elliptical"], met: 5.0, category: "cardio", icon: "figure.elliptical", highImpact: false},

        // Sức mạnh
        {id: "gym", name: "Tập tạ / gym", aliases: ["weight lifting", "gym", "ta"], met: 5.0, category: "strength", icon: "dumbbell", highImpact: false},
        {id: "bodyweight", name: "Bài tập tại nhà (squat, chống đẩy…)", aliases: ["bodyweight", "calisthenics", "tai nha"], met: 3.8, category: "strength", icon: "figure.strengthtraining.functional", highImpact: false},
        {id: "hiit", name: "HIIT cường độ cao", aliases: ["hiit", "circuit"], met: 8.0, category: "strength", icon: "figure.highintensity.intervaltraining", highImpact: true},

        // Thể thao
        {id: "badminton", name: "Cầu lông", aliases: ["badminton", "cau long"], met: 5.5, category: "sport", icon: "figure.badminton", highImpact: true},
        {id: "football", name: "Bóng đá", aliases: ["soccer", "football", "da bong"], met: 7.0, category: "sport", icon: "figure.soccer", highImpact: true},
        {id: "basketball", name: "Bóng rổ", aliases: ["basketball"], met: 6.5, category: "sport", icon: "figure.basketball", highImpact: true},
        {id: "volleyball", name: "Bóng chuyền", aliases: ["volleyball"], met: 4.0, category: "sport", icon: "figure.volleyball", highImpact: true},
        {id: "tennis", name: "Quần vợt", aliases: ["tennis"], met: 7.3, category: "sport", icon: "figure.tennis", highImpact: true},
        {id: "table-tennis", name: "Bóng bàn", aliases: ["table tennis", "ping pong"], met: 4.0, category: "sport", icon: "figure.table.tennis", highImpact: false},
        {id: "martial-arts", name: "Võ thuật", aliases: ["martial arts", "vo", "boxing"], met: 10.3, category: "sport", icon: "figure.martial.arts", highImpact: true},

        // Dẻo dai
        {id: "yoga", name: "Yoga", aliases: ["yoga"], met: 2.5, category: "flexibility", icon: "figure.yoga", highImpact: false},
        {id: "stretching", name: "Giãn cơ", aliases: ["stretching", "gian co"], met: 2.3, category: "flexibility", icon: "figure.flexibility", highImpact: false},
        {id: "pilates", name: "Pilates", aliases: ["pilates"], met: 3.0, category: "flexibility", icon: "figure.pilates", highImpact: false},
        {id: "tai-chi", name: "Thái cực quyền / dưỡng sinh", aliases: ["tai chi", "duong sinh"], met: 3.0, category: "flexibility", icon: "figure.taichi", highImpact: false},

        // Hằng ngày
        {id: "housework", name: "Làm việc nhà (lau dọn)", aliases: ["housework", "don nha"], met: 3.3, category: "daily", icon: "house", highImpact: false},
        {id: "gardening", name: "Làm vườn", aliases: ["gardening"], met: 3.8, category: "daily", icon: "leaf", highImpact: false},
        {id: "dancing", name: "Khiêu vũ / nhảy", aliases: ["dancing", "khieu vu"], met: 5.0, category: "daily", icon: "figure.socialdance", highImpact: false},
        {id: "play-kids", name: "Chơi đùa cùng con", aliases: ["playing with kids"], met: 3.5, category: "daily", icon: "figure.and.child.holdinghands", highImpact: false},
    
];

export const exerciseById = (id: string) => EXERCISES.find((e) => e.id === id);

export function searchExercises(query: string): Exercise[] {
  const q = searchKey(query);
  if (!q) return EXERCISES;
  return EXERCISES.filter((e) => [e.name, ...e.aliases].some((s) => searchKey(s).includes(q)));
}

/** Động tác tập tại nhà không cần dụng cụ. */
export interface HomeMove {
  id: string;
  name: string;
  icon: string;
  target: string;
  reps: string;
  steps: string[];
  easier: string;
  caution: string;
}

export const HOME_MOVES: HomeMove[] = [

        {id: "squat", name: "Squat (ngồi xổm)", icon: "figure.strengthtraining.functional", target: "Đùi, mông",
                 reps: "3 hiệp × 10–15 lần",
                 steps: ["Đứng chân rộng bằng vai, mũi chân hơi mở", "Đẩy hông ra sau như ngồi xuống ghế, lưng thẳng", "Hạ đến khi đùi gần song song sàn rồi đứng lên"],
                 easier: "Ngồi xuống ghế thật rồi đứng lên", caution: "Đầu gối đi cùng hướng mũi chân, không chụm vào trong."},
        {id: "pushup", name: "Chống đẩy", icon: "figure.strengthtraining.traditional", target: "Ngực, tay sau, vai",
                 reps: "3 hiệp × 8–12 lần",
                 steps: ["Hai tay rộng hơn vai, người thẳng từ đầu tới gót", "Hạ ngực xuống gần sàn, khuỷu tay chếch khoảng 45°", "Đẩy người lên"],
                 easier: "Chống đẩy tựa tường hoặc quỳ gối", caution: "Không võng lưng hay đẩy mông lên cao."},
        {id: "plank", name: "Plank", icon: "figure.core.training", target: "Cơ bụng, lưng",
                 reps: "3 lần × 20–45 giây",
                 steps: ["Chống khuỷu tay dưới vai", "Người thẳng, siết bụng và mông", "Giữ và thở đều"],
                 easier: "Plank quỳ gối", caution: "Dừng nếu đau lưng dưới."},
        {id: "lunge", name: "Lunge (chùng chân)", icon: "figure.step.training", target: "Đùi, mông, thăng bằng",
                 reps: "3 hiệp × 10 lần mỗi chân",
                 steps: ["Bước một chân lên trước", "Hạ người đến khi hai gối gập khoảng 90°", "Đẩy chân trước để về vị trí đứng"],
                 easier: "Vịn ghế hoặc tường để giữ thăng bằng", caution: "Gối trước không vượt quá mũi chân nhiều."},
        {id: "bridge", name: "Glute bridge (nâng hông)", icon: "figure.cooldown", target: "Mông, lưng dưới",
                 reps: "3 hiệp × 12–15 lần",
                 steps: ["Nằm ngửa, co gối, bàn chân trên sàn", "Siết mông đẩy hông lên thành đường thẳng vai–gối", "Giữ 2 giây rồi hạ xuống"],
                 easier: "Giảm biên độ nâng hông", caution: "Không ưỡn lưng quá mức."},
        {id: "jumping-jack", name: "Jumping jack (bật nhảy dang tay)", icon: "figure.mixed.cardio", target: "Tim mạch, toàn thân",
                 reps: "3 lần × 30–45 giây",
                 steps: ["Bật nhảy dang chân, đồng thời đưa tay lên cao", "Bật về khép chân, hạ tay"],
                 easier: "Bước sang ngang thay vì bật nhảy", caution: "Người thừa cân nhiều hoặc đau khớp gối nên dùng bản không nhảy."},
        {id: "mountain-climber", name: "Mountain climber (leo núi tại chỗ)", icon: "figure.highintensity.intervaltraining", target: "Bụng, tim mạch",
                 reps: "3 lần × 20–30 giây",
                 steps: ["Tư thế chống đẩy tay thẳng", "Lần lượt kéo gối về phía ngực thật nhanh"],
                 easier: "Làm chậm, chống tay lên ghế", caution: "Giữ hông thấp, không nhổm mông."},
        {id: "crunch", name: "Gập bụng (crunch)", icon: "figure.core.training", target: "Cơ bụng",
                 reps: "3 hiệp × 12–15 lần",
                 steps: ["Nằm ngửa, co gối, tay đặt nhẹ sau đầu", "Siết bụng nâng vai khỏi sàn", "Hạ xuống chậm"],
                 easier: "Giảm số lần, nâng thấp hơn", caution: "Không kéo cổ bằng tay."},
    
];

export interface PlanDay { day: string; title: string; exerciseIDs: string[]; minutes: number }
export interface WorkoutPlan { days: PlanDay[]; notes: string[]; lowImpact: boolean }
export const isRest = (d: PlanDay) => d.exerciseIDs.length === 0;
export const weeklyMinutes = (p: WorkoutPlan) => p.days.reduce((s, d) => s + d.minutes, 0);

/** Tập nhẹ nhàng cho khớp khi BMI béo phì hoặc từ 60 tuổi. */
export const needsLowImpact = (age: number, category?: BMICategory) =>
  age >= 60 || category === "obese1" || category === "obese2";

export function workoutPlan(goal: WeightGoal, age: number, category?: BMICategory): WorkoutPlan {
  const low = needsLowImpact(age, category);
  const cardio = low ? ["walk-brisk", "cycle-easy", "swim-easy"] : ["walk-brisk", "jog", "cycle-moderate", "swim-easy"];
  const intense = low ? ["swim-easy", "elliptical"] : ["hiit", "jump-rope", "run"];
  const strength = ["bodyweight", "gym"];
  const flex = low ? ["tai-chi", "stretching"] : ["yoga", "stretching"];
  const d = (day: string, title: string, ids: string[], minutes: number): PlanDay => ({ day, title, exerciseIDs: ids, minutes });
  const days: PlanDay[] =
    goal === "lose"
      ? [d("Thứ 2", "Cardio", cardio, 40), d("Thứ 3", "Sức mạnh toàn thân", strength, 30), d("Thứ 4", "Cardio", cardio, 40),
         d("Thứ 5", "Dẻo dai", flex, 30), d("Thứ 6", low ? "Cardio nhẹ" : "Cardio cường độ cao", intense, low ? 40 : 25),
         d("Thứ 7", "Sức mạnh toàn thân", strength, 30), d("Chủ nhật", "Nghỉ / đi bộ nhẹ", [], 0)]
      : goal === "maintain"
        ? [d("Thứ 2", "Cardio", cardio, 30), d("Thứ 3", "Sức mạnh", strength, 30), d("Thứ 4", "Nghỉ", [], 0),
           d("Thứ 5", "Cardio", cardio, 30), d("Thứ 6", "Sức mạnh", strength, 30),
           d("Thứ 7", "Thể thao / dẻo dai", low ? flex : ["badminton", "football", "yoga"], 45), d("Chủ nhật", "Nghỉ", [], 0)]
        : [d("Thứ 2", "Sức mạnh: thân dưới", strength, 45), d("Thứ 3", "Nghỉ", [], 0), d("Thứ 4", "Sức mạnh: thân trên", strength, 45),
           d("Thứ 5", "Cardio nhẹ", ["walk-brisk", "cycle-easy"], 20), d("Thứ 6", "Sức mạnh toàn thân", strength, 45),
           d("Thứ 7", "Dẻo dai", flex, 30), d("Chủ nhật", "Nghỉ", [], 0)];
  const notes = [
    "WHO khuyến nghị người lớn tập 150–300 phút cường độ vừa mỗi tuần và ít nhất 2 buổi tăng cơ.",
    "Khởi động 5–10 phút trước khi tập và giãn cơ sau khi tập.",
    "Mới bắt đầu: tập 50–70% thời gian gợi ý rồi tăng dần mỗi tuần.",
    goal === "lose"
      ? "Giảm cân chủ yếu nhờ ăn uống; tập luyện giúp đốt thêm calo và giữ cơ."
      : goal === "gain"
        ? "Tăng tạ hoặc số lần dần mỗi tuần, ăn đủ đạm và ngủ đủ để cơ phát triển."
        : "Kết hợp cardio và sức mạnh để giữ sức khỏe tim mạch và cơ bắp.",
  ];
  if (low) notes.push("Lịch đã chọn các môn ít tác động lên khớp (đi bộ, đạp xe, bơi). Tránh chạy nhảy nhiều khi mới bắt đầu.");
  notes.push("Dừng tập và đi khám nếu đau ngực, khó thở bất thường, chóng mặt. Người có bệnh tim, huyết áp, tiểu đường nên hỏi bác sĩ trước.");
  return { days, notes, lowImpact: low };
}
