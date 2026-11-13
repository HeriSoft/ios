import Foundation
import SwiftData

/// Mở thẳng một màn hình với dữ liệu mẫu, ví dụ: `-demoScreen detail`.
/// Dùng trên GitHub Actions để chụp màn hình app mà không cần camera.
enum DemoScreen: String {
    case scan, detail, label, log
}

enum DemoMode {
    static let current: DemoScreen? = UserDefaults.standard
        .string(forKey: "demoScreen")
        .flatMap(DemoScreen.init(rawValue:))

    static var initialTab: AppTab {
        current == .log ? .log : .scan
    }

    static var initialScanPath: [ScanRoute] {
        switch current {
        case .detail: return [.product(DemoData.sampleProduct)]
        case .label: return [.label(barcode: nil)]
        default: return []
        }
    }
}

enum DemoData {
    static let sampleProduct = ProductInfo(
        barcode: "8930000000017",
        name: "Bánh quy bơ (mẫu)",
        brand: "Sản phẩm demo",
        quantityText: "300 g",
        servingSizeText: "30 g (3 cái)",
        servingGrams: 30,
        kcalPer100g: 480,
        protein100g: 6.2,
        carbs100g: 64.5,
        sugars100g: 22,
        fat100g: 21.4,
        source: .openFoodFacts
    )

    static let labelLines = [
        "THÔNG TIN DINH DƯỠNG",
        "Giá trị dinh dưỡng trong 100 g",
        "Năng lượng 2008 kJ / 480 kcal",
        "Chất đạm 6,2 g",
        "Carbohydrate 64,5 g",
        "Chất béo 21,4 g",
    ]

    @MainActor
    static func seedIfNeeded(_ context: ModelContext) {
        guard DemoMode.current == .log else { return }
        let existing = (try? context.fetchCount(FetchDescriptor<FoodEntry>())) ?? 0
        guard existing == 0 else { return }

        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        func at(_ dayOffset: Int, _ hour: Int, _ minute: Int = 0) -> Date {
            let day = calendar.date(byAdding: .day, value: dayOffset, to: today) ?? today
            return calendar.date(bySettingHour: hour, minute: minute, second: 0, of: day) ?? day
        }

        let samples: [FoodEntry] = [
            FoodEntry(date: at(0, 7, 30), name: "Sữa chua có đường", amount: 100, unit: "g", kcal: 99),
            FoodEntry(date: at(0, 7, 35), name: "Bánh mì sandwich", amount: 2, unit: "phần", kcal: 260),
            FoodEntry(date: at(0, 12, 10), name: "Mì ăn liền", amount: 1, unit: "phần", kcal: 350),
            FoodEntry(date: at(0, 15, 0), name: "Bánh quy bơ (mẫu)", amount: 30, unit: "g", kcal: 144),
            FoodEntry(date: at(-1, 8, 0), name: "Ngũ cốc ăn sáng", amount: 40, unit: "g", kcal: 152),
            FoodEntry(date: at(-1, 19, 30), name: "Nước ngọt có ga", amount: 330, unit: "g", kcal: 139),
        ]
        for sample in samples { context.insert(sample) }
        try? context.save()
    }
}
