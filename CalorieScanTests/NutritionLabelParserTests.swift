import XCTest
@testable import CalorieScan

final class NutritionLabelParserTests: XCTestCase {
    func testVietnameseLabelPer100g() {
        let result = NutritionLabelParser.parse(lines: [
            "THÔNG TIN DINH DƯỠNG",
            "Giá trị dinh dưỡng trong 100 g",
            "Năng lượng 2008 kJ / 480 kcal",
            "Chất đạm 6,2 g",
        ])
        XCTAssertEqual(result.kcal, 480)
        XCTAssertEqual(result.basis, .per100g)
    }

    func testKcalBeforeValue() {
        let result = NutritionLabelParser.parse(lines: ["Energy (kcal) 250", "per 100ml"])
        XCTAssertEqual(result.kcal, 250)
        XCTAssertEqual(result.basis, .per100g)
    }

    func testUSNutritionFacts() {
        let result = NutritionLabelParser.parse(lines: [
            "Nutrition Facts",
            "Serving size 2/3 cup (55g)",
            "Calories 230",
            "Total Fat 8g",
            "2,000 calories a day is used for general nutrition advice.",
        ])
        XCTAssertEqual(result.kcal, 230)
        XCTAssertEqual(result.basis, .perServing)
        XCTAssertEqual(result.servingGrams, 55)
    }

    func testDecimalComma() {
        let result = NutritionLabelParser.parse(lines: ["Năng lượng: 52,5 kcal/100ml"])
        XCTAssertEqual(result.kcal, 52.5)
    }

    func testKilojouleOnly() throws {
        let result = NutritionLabelParser.parse(lines: ["Energy 1000 kJ per 100 g"])
        XCTAssertEqual(try XCTUnwrap(result.kcal), 239, accuracy: 0.1)
    }

    func testTwoColumns() {
        let result = NutritionLabelParser.parse(lines: ["Trong 100 g | Khẩu phần 30 g", "Năng lượng 539 kcal 162 kcal"])
        XCTAssertEqual(result.kcal, 539)
        XCTAssertEqual(result.allKcalValues, [539, 162])
        XCTAssertEqual(result.servingGrams, 30)
    }

    func testNoEnergyFound() {
        let result = NutritionLabelParser.parse(lines: ["Hello world", "Thành phần: bột mì, đường"])
        XCTAssertNil(result.kcal)
    }
}
