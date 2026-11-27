import Foundation

struct FoodSuggestion: Identifiable, Hashable {
    let food: FoodItem
    let reason: String
    var id: String { food.id }
}

struct NutritionAdvice {
    let eatMore: [FoodSuggestion]
    let limit: [FoodSuggestion]
    let tips: [String]
}

/// Gợi ý thực phẩm theo mục tiêu và chỉ số cơ thể (lời khuyên chung, không thay thế chuyên gia).
enum NutritionAdvisor {
    static let eatMore: [WeightGoal: [(String, String)]] = [
        .lose: [
            ("trung-luoc", "Nhiều đạm, ít calo, giúp no lâu"),
            ("canh-chua", "Nhiều nước và rau, rất ít calo"),
            ("rau-xao", "Chất xơ giúp no lâu, ít năng lượng"),
            ("goi-cuon", "Nhiều rau, ít dầu mỡ hơn món chiên"),
            ("pho-ga", "Đủ đạm; chọn tô nhỏ, ít bánh phở"),
            ("oi", "Nhiều chất xơ và vitamin C"),
            ("du-du", "Ít calo, tốt cho tiêu hóa"),
            ("dua-hau", "Rất ít calo, nhiều nước"),
        ],
        .maintain: [
            ("ca-kho", "Cá cung cấp đạm và chất béo tốt"),
            ("rau-xao", "Rau xanh mỗi bữa cho đủ chất xơ"),
            ("trung-luoc", "Nguồn đạm rẻ và dễ chế biến"),
            ("com-trang", "Tinh bột vừa đủ: khoảng 1–2 chén mỗi bữa"),
            ("canh-chua", "Bổ sung rau và nước"),
            ("chuoi", "Kali và năng lượng cho buổi tập"),
            ("cam", "Vitamin C, ăn nguyên quả tốt hơn uống nước ép"),
        ],
        .gain: [
            ("bo", "Chất béo tốt, nhiều năng lượng trong khẩu phần nhỏ"),
            ("sinh-to", "Dễ uống thêm calo giữa các bữa"),
            ("trung-chien", "Đạm và năng lượng để tăng cơ"),
            ("com-tam", "Nhiều năng lượng và đạm"),
            ("xoi", "Tinh bột đậm đặc cho bữa sáng"),
            ("chuoi", "Bữa phụ nhanh, nhiều năng lượng"),
            ("sua-tuoi", "Thêm đạm và calo, uống sau khi tập"),
            ("banh-mi-thit", "Bữa phụ tiện lợi, đủ đạm và tinh bột"),
        ],
    ]

    static let limit: [WeightGoal: [(String, String)]] = [
        .lose: [
            ("tra-sua", "Nhiều đường: 1 ly ≈ 1 bữa ăn"),
            ("nuoc-ngot", "Calo rỗng, không giúp no"),
            ("ga-ran", "Nhiều dầu mỡ"),
            ("khoai-tay-chien", "Nhiều dầu, dễ ăn quá nhiều"),
            ("banh-ngot", "Nhiều đường và chất béo"),
            ("cha-gio", "Chiên ngập dầu"),
        ],
        .maintain: [
            ("nuoc-ngot", "Calo rỗng, dễ tăng cân khi uống thường xuyên"),
            ("tra-sua", "Nhiều đường"),
            ("ga-ran", "Nhiều dầu mỡ, nên ăn thỉnh thoảng"),
        ],
        .gain: [
            ("nuoc-ngot", "Calo rỗng, không giúp tăng cơ"),
            ("khoai-tay-chien", "Nên tăng cân bằng thức ăn giàu đạm thay vì đồ chiên"),
        ],
    ]

    static func advice(for profile: BodyProfile, report: BodyReport) -> NutritionAdvice {
        let byID = Dictionary(uniqueKeysWithValues: FoodDatabase.all.map { ($0.id, $0) })
        func suggestions(_ list: [(String, String)]?) -> [FoodSuggestion] {
            (list ?? []).compactMap { id, reason in byID[id].map { FoodSuggestion(food: $0, reason: reason) } }
        }

        var tips: [String] = []
        if !report.isAdult {
            tips.append("Dưới 18 tuổi cần đánh giá theo biểu đồ tăng trưởng theo tuổi. Kết quả ở đây chỉ để tham khảo, hãy hỏi bác sĩ nhi khoa.")
        }
        if profile.goal == .lose && report.category == .underweight {
            tips.append("Bạn đang thiếu cân, không nên giảm cân thêm. Hãy cân nhắc mục tiêu \"Giữ cân\" hoặc \"Tăng cân\".")
        }
        if profile.goal == .gain && (report.category == .obese1 || report.category == .obese2) {
            tips.append("Chỉ số BMI đang ở mức béo phì, nên hỏi ý kiến bác sĩ trước khi tăng cân.")
        }
        switch report.category {
        case .obese1, .obese2:
            tips.append("BMI ở mức béo phì làm tăng nguy cơ tiểu đường, huyết áp cao và tim mạch. Nên khám sức khỏe định kỳ.")
        case .underweight:
            tips.append("Thiếu cân kéo dài có thể do ăn chưa đủ hoặc vấn đề sức khỏe khác. Nếu sụt cân không rõ lý do, hãy đi khám.")
        default:
            break
        }
        if let ratio = report.waistToHeight, ratio > 0.5 {
            tips.append("Vòng eo lớn hơn một nửa chiều cao: mỡ bụng nhiều, tăng nguy cơ bệnh chuyển hóa. Ưu tiên giảm vòng eo.")
        }
        switch profile.goal {
        case .lose:
            tips.append("Giảm khoảng 0,5 kg mỗi tuần là an toàn. Đừng ăn dưới \(Int(HealthCalculator.minimumKcal(for: profile.sex))) kcal/ngày nếu không có hướng dẫn của chuyên gia.")
        case .gain:
            tips.append("Tăng cân kèm tập sức mạnh 2–3 buổi/tuần để tăng cơ thay vì tăng mỡ.")
        case .maintain:
            tips.append("Giữ cân bằng cách ăn đủ bữa, nhiều rau và theo dõi cân nặng mỗi tuần.")
        }
        tips.append("Ăn khoảng \(Int(report.proteinGrams.rounded())) g đạm mỗi ngày, chia đều các bữa (thịt, cá, trứng, đậu, sữa).")
        tips.append("Uống khoảng \(report.waterLiters.shortText) lít nước mỗi ngày, nhiều hơn khi trời nóng hoặc tập luyện.")

        return NutritionAdvice(
            eatMore: suggestions(eatMore[profile.goal]),
            limit: suggestions(limit[profile.goal]),
            tips: tips
        )
    }
}
