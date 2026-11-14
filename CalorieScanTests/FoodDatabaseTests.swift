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
        // "fruit" là nhãn chung: tính nửa điểm (0.25) nên các món "ramen" (0.3) xếp trước.
        let guesses = FoodDatabase.match(labels: [("banana", 0.9), ("fruit", 0.5), ("ramen", 0.3)])
        XCTAssertEqual(guesses.first?.food.id, "chuoi")
        XCTAssertEqual(guesses.first?.confidence, 0.9)
        XCTAssertEqual(guesses.filter { $0.food.id == "chuoi" }.count, 1)
        XCTAssertTrue(guesses.contains { $0.food.id == "pho-bo" })
        XCTAssertLessThanOrEqual(guesses.count, 6)
    }

    func testMatchUnderscoreIdentifiers() {
        let guesses = FoodDatabase.match(labels: [("fried_chicken", 0.8)])
        XCTAssertEqual(guesses.first?.food.id, "ga-ran")
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

    /// Mọi nhãn trong bảng phải là nhãn mà bộ phân loại Vision thật sự hỗ trợ.
    func testAllVisionLabelsAreSupported() throws {
        let supported = Set(FoodClassifier.supportedIdentifiers().map(FoodDatabase.normalizeLabel))
        print("VISION supported identifiers: \(supported.count)")
        try XCTSkipIf(supported.isEmpty, "Vision không trả về danh sách nhãn trên máy này")
        let used = Set(FoodDatabase.all.flatMap(\.visionLabels))
        let unsupported = used.subtracting(supported).sorted()
        XCTAssertTrue(unsupported.isEmpty, "VISION unsupported labels in table: \(unsupported.joined(separator: ", "))")
        XCTAssertTrue(FoodDatabase.genericLabels.isSubset(of: supported))
    }
}
