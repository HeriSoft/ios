import Foundation

struct NutritionLabelResult: Equatable {
    enum Basis: String, CaseIterable, Hashable {
        case per100g
        case perServing
    }

    var kcal: Double?
    var basis: Basis
    var servingGrams: Double?
    /// Tất cả giá trị kcal tìm thấy (ví dụ cột 100 g và cột khẩu phần).
    var allKcalValues: [Double]
}

/// Tìm số calo trong văn bản OCR của nhãn dinh dưỡng (tiếng Việt hoặc tiếng Anh).
enum NutritionLabelParser {
    private static let number = #"(\d+(?:\.\d+)?)"#

    static func parse(lines: [String]) -> NutritionLabelResult {
        let text = normalize(lines.joined(separator: " \n "))

        // 1) "480 kcal"  2) "(kcal) 480"  3) "Calories 230" / "Calo: 230"
        let numberBeforeKcal = values(number + #"\s*k\s?ca[l1i]"#, in: text)
        let numberAfterKcal = values(#"kca[l1i]\)?\s*[:\-/]?\s*"# + number, in: text)
        let calories = values(#"calo(?:ries?)?\s*[:\-]?\s*"# + number, in: text)
        // 4) Chỉ có kJ
        let kilojoules = values(number + #"\s*kj"#, in: text).map(CalorieCalculator.kJToKcal)

        let plausible: (Double) -> Bool = { $0 > 0 && $0 <= 2000 }
        let candidates = [numberBeforeKcal, numberAfterKcal, calories, kilojoules]
            .map { $0.filter(plausible) }
        let kcal = candidates.first(where: { !$0.isEmpty })?.first

        let mentions100 = !values(#"(100)\s?(?:g|ml)\b"#, in: text).isEmpty
        let mentionsServing = text.range(
            of: #"serving|khau phan|phan an|moi phan|1 phan|per pack|portion"#,
            options: .regularExpression
        ) != nil
        let basis: NutritionLabelResult.Basis = (!mentions100 && mentionsServing) ? .perServing : .per100g

        let servingGrams = values(
            #"(?:serving size|per serving|khau phan|phan an|moi phan|1 phan|portion)[\s\S]{0,40}?"# + number + #"\s*(?:g|ml)\b"#,
            in: text
        ).first(where: { $0 > 0 && $0 < 2000 })

        return NutritionLabelResult(
            kcal: kcal,
            basis: basis,
            servingGrams: servingGrams,
            allKcalValues: numberBeforeKcal.filter(plausible)
        )
    }

    /// Chữ thường, bỏ dấu tiếng Việt, đổi dấu phẩy thập phân thành dấu chấm.
    static func normalize(_ text: String) -> String {
        var result = text
            .replacingOccurrences(of: "đ", with: "d")
            .replacingOccurrences(of: "Đ", with: "D")
            .folding(options: [.diacriticInsensitive, .caseInsensitive], locale: Locale(identifier: "en_US_POSIX"))
            .lowercased()
        result = result.replacingOccurrences(of: #"(\d),(\d)"#, with: "$1.$2", options: .regularExpression)
        return result
    }

    /// Giá trị số của nhóm bắt (capture group) đầu tiên cho mỗi lần khớp.
    private static func values(_ pattern: String, in text: String) -> [Double] {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let ns = text as NSString
        return regex.matches(in: text, range: NSRange(location: 0, length: ns.length)).compactMap { match in
            guard match.numberOfRanges > 1 else { return nil }
            let range = match.range(at: 1)
            guard range.location != NSNotFound else { return nil }
            return Double(ns.substring(with: range))
        }
    }
}
