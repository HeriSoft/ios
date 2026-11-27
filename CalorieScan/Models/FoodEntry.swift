import Foundation
import SwiftData

/// Một món đã ăn được ghi vào nhật ký.
@Model
final class FoodEntry {
    var date: Date
    var name: String
    var brand: String?
    var barcode: String?
    var amount: Double
    /// "g" hoặc "phần".
    var unit: String
    var kcal: Double

    init(date: Date = .now, name: String, brand: String? = nil, barcode: String? = nil,
         amount: Double, unit: String, kcal: Double) {
        self.date = date
        self.name = name
        self.brand = brand
        self.barcode = barcode
        self.amount = amount
        self.unit = unit
        self.kcal = kcal
    }
}
