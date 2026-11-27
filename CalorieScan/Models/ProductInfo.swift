import Foundation

/// Thông tin dinh dưỡng của một sản phẩm (từ Open Food Facts, từ nhãn, hoặc tự nhập).
struct ProductInfo: Hashable, Identifiable {
    enum Source: String, Hashable {
        case openFoodFacts
        case label
        case manual
        /// Giá trị ước tính từ bảng món ăn.
        case estimate
    }

    var barcode: String? = nil
    var name: String
    var brand: String? = nil
    var imageURL: URL? = nil
    var quantityText: String? = nil
    var servingSizeText: String? = nil
    /// Khối lượng một khẩu phần (g hoặc ml).
    var servingGrams: Double? = nil
    var kcalPer100g: Double? = nil
    var kcalPerServing: Double? = nil
    var protein100g: Double? = nil
    var carbs100g: Double? = nil
    var sugars100g: Double? = nil
    var fat100g: Double? = nil
    var source: Source = .manual

    var id: String { barcode ?? name }

    /// Calo mỗi khẩu phần: lấy trực tiếp, hoặc tính từ kcal/100g và khối lượng khẩu phần.
    var effectiveKcalPerServing: Double? {
        if let kcalPerServing { return kcalPerServing }
        if let kcalPer100g, let servingGrams, servingGrams > 0 {
            return CalorieCalculator.kcal(per100g: kcalPer100g, amount: servingGrams)
        }
        return nil
    }
}
