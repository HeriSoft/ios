import Foundation

/// Phân loại BMI cho người trưởng thành châu Á (WHO khu vực Tây Thái Bình Dương, Bộ Y tế Việt Nam áp dụng).
enum BMICategory: Equatable {
    case underweight, normal, overweight, obese1, obese2

    init(bmi: Double) {
        switch bmi {
        case ..<18.5: self = .underweight
        case ..<23: self = .normal
        case ..<25: self = .overweight
        case ..<30: self = .obese1
        default: self = .obese2
        }
    }

    var title: String {
        switch self {
        case .underweight: return "Thiếu cân"
        case .normal: return "Bình thường"
        case .overweight: return "Thừa cân"
        case .obese1: return "Béo phì độ I"
        case .obese2: return "Béo phì độ II"
        }
    }
}

struct BodyReport: Equatable {
    let bmi: Double
    let category: BMICategory
    /// Cân nặng ứng với BMI 18,5–22,9.
    let healthyWeightRange: ClosedRange<Double>
    /// Số kg cần thay đổi để vào khoảng hợp lý: dương = cần tăng, âm = cần giảm, 0 = đã hợp lý.
    let weightChangeToHealthy: Double
    let bmr: Double
    let tdee: Double
    let targetKcal: Double
    let proteinGrams: Double
    let fatGrams: Double
    let carbGrams: Double
    let waterLiters: Double
    /// % mỡ ước tính theo công thức Deurenberg (chỉ cho người ≥ 18 tuổi).
    let bodyFatPercent: Double?
    let waistToHeight: Double?
    let isAdult: Bool
}

enum HealthCalculator {
    static let healthyBMI: ClosedRange<Double> = 18.5...22.9

    static func bmi(weightKg: Double, heightCm: Double) -> Double {
        let meters = heightCm / 100
        return weightKg / (meters * meters)
    }

    /// Năng lượng cơ thể tiêu hao khi nghỉ ngơi (Mifflin-St Jeor).
    static func bmr(_ p: BodyProfile) -> Double {
        let base = 10 * p.weightKg + 6.25 * p.heightCm - 5 * Double(p.age)
        return base + (p.sex == .male ? 5 : -161)
    }

    /// Calo tối thiểu nên ăn mỗi ngày khi giảm cân, không nên thấp hơn.
    static func minimumKcal(for sex: Sex) -> Double {
        sex == .female ? 1200 : 1500
    }

    static func report(for p: BodyProfile) -> BodyReport? {
        guard p.isValid else { return nil }

        let bmi = bmi(weightKg: p.weightKg, heightCm: p.heightCm)
        let meters2 = pow(p.heightCm / 100, 2)
        let range = (healthyBMI.lowerBound * meters2)...(healthyBMI.upperBound * meters2)
        let change: Double
        if p.weightKg < range.lowerBound {
            change = range.lowerBound - p.weightKg
        } else if p.weightKg > range.upperBound {
            change = range.upperBound - p.weightKg
        } else {
            change = 0
        }

        let bmr = bmr(p)
        let tdee = bmr * p.activity.factor
        let target: Double
        switch p.goal {
        case .lose:
            // Giảm ~500 kcal/ngày ≈ 0,5 kg/tuần, nhưng không xuống dưới mức tối thiểu.
            target = min(tdee, max(tdee - 500, minimumKcal(for: p.sex)))
        case .maintain:
            target = tdee
        case .gain:
            target = tdee + 300
        }
        let roundedTarget = (target / 10).rounded() * 10

        let proteinPerKg: Double = p.goal == .maintain ? 1.2 : 1.6
        let protein = proteinPerKg * p.weightKg
        let fat = roundedTarget * 0.27 / 9
        let carbs = max(0, (roundedTarget - protein * 4 - fat * 9) / 4)

        let isAdult = p.age >= 18
        let bodyFat: Double? = isAdult
            ? max(3, 1.2 * bmi + 0.23 * Double(p.age) - 10.8 * (p.sex == .male ? 1 : 0) - 5.4)
            : nil

        return BodyReport(
            bmi: bmi,
            category: BMICategory(bmi: bmi),
            healthyWeightRange: range,
            weightChangeToHealthy: change,
            bmr: bmr,
            tdee: tdee,
            targetKcal: roundedTarget,
            proteinGrams: protein,
            fatGrams: fat,
            carbGrams: carbs,
            waterLiters: p.weightKg * 0.035,
            bodyFatPercent: bodyFat,
            waistToHeight: p.waistCm.flatMap { $0 > 0 ? $0 / p.heightCm : nil },
            isAdult: isAdult
        )
    }
}
