import XCTest
@testable import CalorieScan

final class FoodDatabaseTests: XCTestCase {
    func testIDsAreUniqueAndValuesPlausible() {
        let ids = FoodDatabase.all.map(\.id)
        XCTAssertEqual(Set(ids).count, ids.count, "Duplicate food IDs")
        for food in FoodDatabase.all {
            XCTAssertTrue((10...950).contains(food.kcalPer100g), "\(food.name): kcal/100g out of range")
            XCTAssertGreaterThan(food.portionGrams, 0, food.name)
            XCTAssertFalse(food.visionLabels.isEmpty, food.name)
            for label in food.visionLabels {
                XCTAssertEqual(label, FoodDatabase.normalizeLabel(label), "\(food.name): label '\(label)' not normalized")
            }
        }
    }

    func testMatchSortsByConfidenceAndDeduplicates() {
        let guesses = FoodDatabase.match(labels: [("banana", 0.9), ("fruit", 0.5), ("noodles", 0.3)])
        XCTAssertEqual(guesses.first?.food.id, "chuoi")
        XCTAssertEqual(guesses.first?.confidence, 0.9)
        XCTAssertEqual(guesses.filter { $0.food.id == "chuoi" }.count, 1)
        XCTAssertTrue(guesses.contains { $0.food.id == "pho-bo" })
        XCTAssertLessThanOrEqual(guesses.count, 6)
    }

    func testMatchUnderscoreIdentifiers() {
        let guesses = FoodDatabase.match(labels: [("french_fries", 0.8)])
        XCTAssertEqual(guesses.first?.food.id, "khoai-tay-chien")
    }

    func testNoFoodLabels() {
        XCTAssertTrue(FoodDatabase.match(labels: [("car", 0.9), ("sky", 0.8)]).isEmpty)
    }

    func testSearchIgnoresDiacritics() {
        XCTAssertTrue(FoodDatabase.search("pho").contains { $0.id == "pho-bo" })
        XCTAssertTrue(FoodDatabase.search("Cơm Tấm").contains { $0.id == "com-tam" })
        XCTAssertTrue(FoodDatabase.search("dua hau").contains { $0.id == "dua-hau" })
        XCTAssertTrue(FoodDatabase.search("banana").contains { $0.id == "chuoi" })
        XCTAssertEqual(FoodDatabase.search("").count, FoodDatabase.all.count)
        XCTAssertTrue(FoodDatabase.search("xyz123").isEmpty)
    }

    func testPortionCalories() throws {
        let pho = try XCTUnwrap(FoodDatabase.all.first { $0.id == "pho-bo" })
        XCTAssertEqual(pho.kcalPerPortion, 450, accuracy: 0.01)
        XCTAssertEqual(pho.productInfo.effectiveKcalPerServing ?? 0, 450, accuracy: 0.01)
        XCTAssertEqual(pho.productInfo.source, .estimate)
    }

    /// In ra (không làm test thất bại) các nhãn trong bảng mà bộ phân loại Vision không hỗ trợ,
    /// cùng các nhãn đồ ăn Vision hỗ trợ — dùng để cải thiện bảng món ăn.
    func testReportVisionLabelCoverage() {
        let supported = Set(FoodClassifier.supportedIdentifiers().map(FoodDatabase.normalizeLabel))
        print("VISION supported identifiers: \(supported.count)")
        guard !supported.isEmpty else { return }
        let used = Set(FoodDatabase.all.flatMap(\.visionLabels))
        print("VISION unsupported labels in table: \(used.subtracting(supported).sorted().joined(separator: ", "))")
        print("VISION all identifiers: \(supported.sorted().joined(separator: ", "))")
    }
}
