import Foundation

enum CalorieCalculator {
    /// Calo cho `amount` gram/ml khi biết calo trên 100 g/ml.
    static func kcal(per100g: Double, amount: Double) -> Double {
        max(0, per100g * amount / 100)
    }

    /// Calo cho `servings` khẩu phần.
    static func kcal(perServing: Double, servings: Double) -> Double {
        max(0, perServing * servings)
    }

    static func kJToKcal(_ kilojoules: Double) -> Double {
        kilojoules / 4.184
    }
}

extension Double {
    var kcalText: String { "\(Int(rounded())) kcal" }

    var shortText: String { formatted(.number.precision(.fractionLength(0...1))) }
}
