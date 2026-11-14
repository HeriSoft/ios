import Foundation
import SwiftData

enum ExerciseCategory: String, CaseIterable, Identifiable {
    case cardio, strength, sport, flexibility, daily
    var id: Self { self }

    var title: String {
        switch self {
        case .cardio: return "Cardio"
        case .strength: return "Sức mạnh"
        case .sport: return "Thể thao"
        case .flexibility: return "Dẻo dai & thư giãn"
        case .daily: return "Hoạt động hằng ngày"
        }
    }
}

/// Một môn tập với hệ số MET (theo Compendium of Physical Activities).
struct Exercise: Identifiable, Hashable {
    let id: String
    let name: String
    let aliases: [String]
    let met: Double
    let category: ExerciseCategory
    let icon: String
    /// Có nhảy/chạy, tác động mạnh lên khớp.
    let highImpact: Bool

    /// Calo đốt: MET × 3,5 × cân nặng (kg) / 200 × số phút.
    func kcal(weightKg: Double, minutes: Double) -> Double {
        ExerciseLibrary.kcal(met: met, weightKg: weightKg, minutes: minutes)
    }
}

/// Một buổi tập đã ghi vào nhật ký.
@Model
final class WorkoutEntry {
    var date: Date
    var name: String
    var exerciseID: String
    var minutes: Double
    var kcal: Double

    init(date: Date = .now, name: String, exerciseID: String, minutes: Double, kcal: Double) {
        self.date = date
        self.name = name
        self.exerciseID = exerciseID
        self.minutes = minutes
        self.kcal = kcal
    }
}

enum ExerciseLibrary {
    static func kcal(met: Double, weightKg: Double, minutes: Double) -> Double {
        max(0, met * 3.5 * weightKg / 200 * minutes)
    }

    static let all: [Exercise] = [
        // Cardio
        Exercise(id: "walk-slow", name: "Đi bộ chậm", aliases: ["walking", "di bo"], met: 2.8, category: .cardio, icon: "figure.walk", highImpact: false),
        Exercise(id: "walk-brisk", name: "Đi bộ nhanh", aliases: ["brisk walking", "di bo nhanh"], met: 4.3, category: .cardio, icon: "figure.walk.motion", highImpact: false),
        Exercise(id: "jog", name: "Chạy bộ chậm (~8 km/h)", aliases: ["jogging", "chay bo"], met: 8.3, category: .cardio, icon: "figure.run", highImpact: true),
        Exercise(id: "run", name: "Chạy bộ (~10 km/h)", aliases: ["running", "chay"], met: 9.8, category: .cardio, icon: "figure.run", highImpact: true),
        Exercise(id: "cycle-easy", name: "Đạp xe nhẹ", aliases: ["cycling", "xe dap"], met: 4.0, category: .cardio, icon: "figure.outdoor.cycle", highImpact: false),
        Exercise(id: "cycle-moderate", name: "Đạp xe vừa (~20 km/h)", aliases: ["cycling", "xe dap"], met: 8.0, category: .cardio, icon: "figure.outdoor.cycle", highImpact: false),
        Exercise(id: "swim-easy", name: "Bơi nhẹ nhàng", aliases: ["swimming", "boi"], met: 6.0, category: .cardio, icon: "figure.pool.swim", highImpact: false),
        Exercise(id: "swim-fast", name: "Bơi nhanh", aliases: ["swimming", "boi"], met: 9.8, category: .cardio, icon: "figure.pool.swim", highImpact: false),
        Exercise(id: "jump-rope", name: "Nhảy dây", aliases: ["jump rope", "nhay day"], met: 11.8, category: .cardio, icon: "figure.jumprope", highImpact: true),
        Exercise(id: "stairs", name: "Leo cầu thang", aliases: ["stairs", "cau thang"], met: 8.0, category: .cardio, icon: "figure.stairs", highImpact: false),
        Exercise(id: "aerobic", name: "Aerobic / Zumba", aliases: ["aerobic", "zumba"], met: 7.3, category: .cardio, icon: "figure.dance", highImpact: true),
        Exercise(id: "elliptical", name: "Máy tập elip", aliases: ["elliptical"], met: 5.0, category: .cardio, icon: "figure.elliptical", highImpact: false),

        // Sức mạnh
        Exercise(id: "gym", name: "Tập tạ / gym", aliases: ["weight lifting", "gym", "ta"], met: 5.0, category: .strength, icon: "dumbbell", highImpact: false),
        Exercise(id: "bodyweight", name: "Bài tập tại nhà (squat, chống đẩy…)", aliases: ["bodyweight", "calisthenics", "tai nha"], met: 3.8, category: .strength, icon: "figure.strengthtraining.functional", highImpact: false),
        Exercise(id: "hiit", name: "HIIT cường độ cao", aliases: ["hiit", "circuit"], met: 8.0, category: .strength, icon: "figure.highintensity.intervaltraining", highImpact: true),

        // Thể thao
        Exercise(id: "badminton", name: "Cầu lông", aliases: ["badminton", "cau long"], met: 5.5, category: .sport, icon: "figure.badminton", highImpact: true),
        Exercise(id: "football", name: "Bóng đá", aliases: ["soccer", "football", "da bong"], met: 7.0, category: .sport, icon: "figure.soccer", highImpact: true),
        Exercise(id: "basketball", name: "Bóng rổ", aliases: ["basketball"], met: 6.5, category: .sport, icon: "figure.basketball", highImpact: true),
        Exercise(id: "volleyball", name: "Bóng chuyền", aliases: ["volleyball"], met: 4.0, category: .sport, icon: "figure.volleyball", highImpact: true),
        Exercise(id: "tennis", name: "Quần vợt", aliases: ["tennis"], met: 7.3, category: .sport, icon: "figure.tennis", highImpact: true),
        Exercise(id: "table-tennis", name: "Bóng bàn", aliases: ["table tennis", "ping pong"], met: 4.0, category: .sport, icon: "figure.table.tennis", highImpact: false),
        Exercise(id: "martial-arts", name: "Võ thuật", aliases: ["martial arts", "vo", "boxing"], met: 10.3, category: .sport, icon: "figure.martial.arts", highImpact: true),

        // Dẻo dai
        Exercise(id: "yoga", name: "Yoga", aliases: ["yoga"], met: 2.5, category: .flexibility, icon: "figure.yoga", highImpact: false),
        Exercise(id: "stretching", name: "Giãn cơ", aliases: ["stretching", "gian co"], met: 2.3, category: .flexibility, icon: "figure.flexibility", highImpact: false),
        Exercise(id: "pilates", name: "Pilates", aliases: ["pilates"], met: 3.0, category: .flexibility, icon: "figure.pilates", highImpact: false),
        Exercise(id: "tai-chi", name: "Thái cực quyền / dưỡng sinh", aliases: ["tai chi", "duong sinh"], met: 3.0, category: .flexibility, icon: "figure.taichi", highImpact: false),

        // Hằng ngày
        Exercise(id: "housework", name: "Làm việc nhà (lau dọn)", aliases: ["housework", "don nha"], met: 3.3, category: .daily, icon: "house", highImpact: false),
        Exercise(id: "gardening", name: "Làm vườn", aliases: ["gardening"], met: 3.8, category: .daily, icon: "leaf", highImpact: false),
        Exercise(id: "dancing", name: "Khiêu vũ / nhảy", aliases: ["dancing", "khieu vu"], met: 5.0, category: .daily, icon: "figure.socialdance", highImpact: false),
        Exercise(id: "play-kids", name: "Chơi đùa cùng con", aliases: ["playing with kids"], met: 3.5, category: .daily, icon: "figure.and.child.holdinghands", highImpact: false),
    ]

    static func exercise(_ id: String) -> Exercise? {
        all.first { $0.id == id }
    }

    static func search(_ query: String) -> [Exercise] {
        let q = FoodDatabase.searchKey(query)
        guard !q.isEmpty else { return all }
        return all.filter { ([$0.name] + $0.aliases).contains { FoodDatabase.searchKey($0).contains(q) } }
    }
}

/// Động tác tập tại nhà không cần dụng cụ.
struct HomeMove: Identifiable, Hashable {
    let id: String
    let name: String
    let icon: String
    let target: String
    let reps: String
    let steps: [String]
    let easier: String
    let caution: String

    static let all: [HomeMove] = [
        HomeMove(id: "squat", name: "Squat (ngồi xổm)", icon: "figure.strengthtraining.functional", target: "Đùi, mông",
                 reps: "3 hiệp × 10–15 lần",
                 steps: ["Đứng chân rộng bằng vai, mũi chân hơi mở", "Đẩy hông ra sau như ngồi xuống ghế, lưng thẳng", "Hạ đến khi đùi gần song song sàn rồi đứng lên"],
                 easier: "Ngồi xuống ghế thật rồi đứng lên", caution: "Đầu gối đi cùng hướng mũi chân, không chụm vào trong."),
        HomeMove(id: "pushup", name: "Chống đẩy", icon: "figure.strengthtraining.traditional", target: "Ngực, tay sau, vai",
                 reps: "3 hiệp × 8–12 lần",
                 steps: ["Hai tay rộng hơn vai, người thẳng từ đầu tới gót", "Hạ ngực xuống gần sàn, khuỷu tay chếch khoảng 45°", "Đẩy người lên"],
                 easier: "Chống đẩy tựa tường hoặc quỳ gối", caution: "Không võng lưng hay đẩy mông lên cao."),
        HomeMove(id: "plank", name: "Plank", icon: "figure.core.training", target: "Cơ bụng, lưng",
                 reps: "3 lần × 20–45 giây",
                 steps: ["Chống khuỷu tay dưới vai", "Người thẳng, siết bụng và mông", "Giữ và thở đều"],
                 easier: "Plank quỳ gối", caution: "Dừng nếu đau lưng dưới."),
        HomeMove(id: "lunge", name: "Lunge (chùng chân)", icon: "figure.step.training", target: "Đùi, mông, thăng bằng",
                 reps: "3 hiệp × 10 lần mỗi chân",
                 steps: ["Bước một chân lên trước", "Hạ người đến khi hai gối gập khoảng 90°", "Đẩy chân trước để về vị trí đứng"],
                 easier: "Vịn ghế hoặc tường để giữ thăng bằng", caution: "Gối trước không vượt quá mũi chân nhiều."),
        HomeMove(id: "bridge", name: "Glute bridge (nâng hông)", icon: "figure.cooldown", target: "Mông, lưng dưới",
                 reps: "3 hiệp × 12–15 lần",
                 steps: ["Nằm ngửa, co gối, bàn chân trên sàn", "Siết mông đẩy hông lên thành đường thẳng vai–gối", "Giữ 2 giây rồi hạ xuống"],
                 easier: "Giảm biên độ nâng hông", caution: "Không ưỡn lưng quá mức."),
        HomeMove(id: "jumping-jack", name: "Jumping jack (bật nhảy dang tay)", icon: "figure.mixed.cardio", target: "Tim mạch, toàn thân",
                 reps: "3 lần × 30–45 giây",
                 steps: ["Bật nhảy dang chân, đồng thời đưa tay lên cao", "Bật về khép chân, hạ tay"],
                 easier: "Bước sang ngang thay vì bật nhảy", caution: "Người thừa cân nhiều hoặc đau khớp gối nên dùng bản không nhảy."),
        HomeMove(id: "mountain-climber", name: "Mountain climber (leo núi tại chỗ)", icon: "figure.highintensity.intervaltraining", target: "Bụng, tim mạch",
                 reps: "3 lần × 20–30 giây",
                 steps: ["Tư thế chống đẩy tay thẳng", "Lần lượt kéo gối về phía ngực thật nhanh"],
                 easier: "Làm chậm, chống tay lên ghế", caution: "Giữ hông thấp, không nhổm mông."),
        HomeMove(id: "crunch", name: "Gập bụng (crunch)", icon: "figure.core.training", target: "Cơ bụng",
                 reps: "3 hiệp × 12–15 lần",
                 steps: ["Nằm ngửa, co gối, tay đặt nhẹ sau đầu", "Siết bụng nâng vai khỏi sàn", "Hạ xuống chậm"],
                 easier: "Giảm số lần, nâng thấp hơn", caution: "Không kéo cổ bằng tay."),
    ]
}

// MARK: - Lịch tập gợi ý

struct PlanDay: Identifiable, Hashable {
    let day: String
    let title: String
    let exerciseIDs: [String]
    let minutes: Int
    var isRest: Bool { exerciseIDs.isEmpty }
    var id: String { day }
}

struct WorkoutPlan {
    let days: [PlanDay]
    let notes: [String]
    let lowImpact: Bool

    var weeklyMinutes: Int { days.reduce(0) { $0 + $1.minutes } }
}

enum WorkoutPlanner {
    /// Tập nhẹ nhàng cho khớp khi BMI béo phì hoặc từ 60 tuổi.
    static func needsLowImpact(age: Int, category: BMICategory?) -> Bool {
        age >= 60 || category == .obese1 || category == .obese2
    }

    static func plan(goal: WeightGoal, age: Int, category: BMICategory?) -> WorkoutPlan {
        let low = needsLowImpact(age: age, category: category)
        let cardio = low ? ["walk-brisk", "cycle-easy", "swim-easy"] : ["walk-brisk", "jog", "cycle-moderate", "swim-easy"]
        let intense = low ? ["swim-easy", "elliptical"] : ["hiit", "jump-rope", "run"]
        let strength = ["bodyweight", "gym"]
        let flex = low ? ["tai-chi", "stretching"] : ["yoga", "stretching"]

        let days: [PlanDay]
        switch goal {
        case .lose:
            days = [
                PlanDay(day: "Thứ 2", title: "Cardio", exerciseIDs: cardio, minutes: 40),
                PlanDay(day: "Thứ 3", title: "Sức mạnh toàn thân", exerciseIDs: strength, minutes: 30),
                PlanDay(day: "Thứ 4", title: "Cardio", exerciseIDs: cardio, minutes: 40),
                PlanDay(day: "Thứ 5", title: "Dẻo dai", exerciseIDs: flex, minutes: 30),
                PlanDay(day: "Thứ 6", title: low ? "Cardio nhẹ" : "Cardio cường độ cao", exerciseIDs: intense, minutes: low ? 40 : 25),
                PlanDay(day: "Thứ 7", title: "Sức mạnh toàn thân", exerciseIDs: strength, minutes: 30),
                PlanDay(day: "Chủ nhật", title: "Nghỉ / đi bộ nhẹ", exerciseIDs: [], minutes: 0),
            ]
        case .maintain:
            days = [
                PlanDay(day: "Thứ 2", title: "Cardio", exerciseIDs: cardio, minutes: 30),
                PlanDay(day: "Thứ 3", title: "Sức mạnh", exerciseIDs: strength, minutes: 30),
                PlanDay(day: "Thứ 4", title: "Nghỉ", exerciseIDs: [], minutes: 0),
                PlanDay(day: "Thứ 5", title: "Cardio", exerciseIDs: cardio, minutes: 30),
                PlanDay(day: "Thứ 6", title: "Sức mạnh", exerciseIDs: strength, minutes: 30),
                PlanDay(day: "Thứ 7", title: "Thể thao / dẻo dai", exerciseIDs: low ? flex : ["badminton", "football", "yoga"], minutes: 45),
                PlanDay(day: "Chủ nhật", title: "Nghỉ", exerciseIDs: [], minutes: 0),
            ]
        case .gain:
            days = [
                PlanDay(day: "Thứ 2", title: "Sức mạnh: thân dưới", exerciseIDs: strength, minutes: 45),
                PlanDay(day: "Thứ 3", title: "Nghỉ", exerciseIDs: [], minutes: 0),
                PlanDay(day: "Thứ 4", title: "Sức mạnh: thân trên", exerciseIDs: strength, minutes: 45),
                PlanDay(day: "Thứ 5", title: "Cardio nhẹ", exerciseIDs: ["walk-brisk", "cycle-easy"], minutes: 20),
                PlanDay(day: "Thứ 6", title: "Sức mạnh toàn thân", exerciseIDs: strength, minutes: 45),
                PlanDay(day: "Thứ 7", title: "Dẻo dai", exerciseIDs: flex, minutes: 30),
                PlanDay(day: "Chủ nhật", title: "Nghỉ", exerciseIDs: [], minutes: 0),
            ]
        }

        var notes = [
            "WHO khuyến nghị người lớn tập 150–300 phút cường độ vừa mỗi tuần và ít nhất 2 buổi tăng cơ.",
            "Khởi động 5–10 phút trước khi tập và giãn cơ sau khi tập.",
            "Mới bắt đầu: tập 50–70% thời gian gợi ý rồi tăng dần mỗi tuần.",
        ]
        switch goal {
        case .lose: notes.append("Giảm cân chủ yếu nhờ ăn uống; tập luyện giúp đốt thêm calo và giữ cơ.")
        case .gain: notes.append("Tăng tạ hoặc số lần dần mỗi tuần, ăn đủ đạm và ngủ đủ để cơ phát triển.")
        case .maintain: notes.append("Kết hợp cardio và sức mạnh để giữ sức khỏe tim mạch và cơ bắp.")
        }
        if low {
            notes.append("Lịch đã chọn các môn ít tác động lên khớp (đi bộ, đạp xe, bơi). Tránh chạy nhảy nhiều khi mới bắt đầu.")
        }
        notes.append("Dừng tập và đi khám nếu đau ngực, khó thở bất thường, chóng mặt. Người có bệnh tim, huyết áp, tiểu đường nên hỏi bác sĩ trước.")

        return WorkoutPlan(days: days, notes: notes, lowImpact: low)
    }
}
