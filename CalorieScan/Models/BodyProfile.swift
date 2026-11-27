import Foundation

enum Sex: String, CaseIterable, Identifiable {
    case male, female
    var id: Self { self }
    var title: String { self == .male ? "Nam" : "Nữ" }
}

enum ActivityLevel: String, CaseIterable, Identifiable {
    case sedentary, light, moderate, active, veryActive
    var id: Self { self }

    /// Hệ số nhân với BMR để ra TDEE.
    var factor: Double {
        switch self {
        case .sedentary: return 1.2
        case .light: return 1.375
        case .moderate: return 1.55
        case .active: return 1.725
        case .veryActive: return 1.9
        }
    }

    var title: String {
        switch self {
        case .sedentary: return "Ít vận động (ngồi nhiều)"
        case .light: return "Nhẹ (tập 1–3 buổi/tuần)"
        case .moderate: return "Vừa (tập 3–5 buổi/tuần)"
        case .active: return "Nhiều (tập 6–7 buổi/tuần)"
        case .veryActive: return "Rất nhiều (lao động nặng)"
        }
    }
}

enum WeightGoal: String, CaseIterable, Identifiable {
    case lose, maintain, gain
    var id: Self { self }

    var title: String {
        switch self {
        case .lose: return "Giảm cân"
        case .maintain: return "Giữ cân"
        case .gain: return "Tăng cân"
        }
    }
}

struct BodyProfile: Equatable {
    var sex: Sex
    var age: Int
    var heightCm: Double
    var weightKg: Double
    var activity: ActivityLevel
    var goal: WeightGoal
    /// Vòng eo (cm), không bắt buộc.
    var waistCm: Double? = nil

    var isValid: Bool {
        (10...100).contains(age) && (100...250).contains(heightCm) && (20...300).contains(weightKg)
    }
}
